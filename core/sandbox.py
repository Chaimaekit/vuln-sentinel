import subprocess
import os
import config


def run_in_sandbox(filepath):
    """
    Runs file in disposable Docker container.
    Collects behavioral evidence safely.
    Container is destroyed after analysis.
    """
    filename = os.path.basename(filepath)
    findings = {
        "executed":         False,
        "strace_output":    "",
        "file_operations":  [],
        "network_attempts": [],
        "shell_spawned":    False,
        "crashed":          False,
        "timed_out":        False,
        "stderr":           ""
    }

    print(f"  [*] Isolating in Docker sandbox: {filename}")

    sandbox_cmd = f"""
        chmod +x /sandbox/{filename} 2>/dev/null; \
        strace -f \
               -e trace=file,network,process \
               -o /tmp/strace.log \
               timeout {config.SANDBOX_TIMEOUT} \
               /sandbox/{filename} < /dev/null 2>/tmp/stderr.log; \
        echo '---STRACE---'; \
        cat /tmp/strace.log 2>/dev/null; \
        echo '---STDERR---'; \
        cat /tmp/stderr.log 2>/dev/null
    """

    try:
        result = subprocess.run([
            "docker", "run",
            "--rm",
            "--network",      "none",
            "--memory",       config.SANDBOX_MEMORY,
            "--cpus",         config.SANDBOX_CPUS,
            "--cap-drop",     "ALL",
            "--security-opt", "no-new-privileges",
            "--tmpfs",        "/tmp:rw,size=64m",
            "-v", f"{filepath}:/sandbox/{filename}:ro",
            config.SANDBOX_IMAGE,
            "bash", "-c", sandbox_cmd
        ],
        capture_output=True,
        text=True,
        timeout=config.SANDBOX_TIMEOUT + 15
        )

        findings["executed"] = True
        output = result.stdout

        if "---STRACE---" in output and "---STDERR---" in output:
            parts = output.split("---STRACE---")
            strace_and_stderr = parts[1].split("---STDERR---")
            findings["strace_output"] = strace_and_stderr[0][:3000]
            findings["stderr"]        = strace_and_stderr[1][:500] \
                                        if len(strace_and_stderr) > 1 else ""
        else:
            findings["strace_output"] = output[:3000]

        for line in findings["strace_output"].splitlines():
            if 'openat(' in line or 'open("' in line:
                findings["file_operations"].append(line.strip())
            if 'connect(' in line or 'socket(' in line:
                findings["network_attempts"].append(line.strip())
            if 'execve("/bin/sh"' in line \
               or 'execve("/bin/bash"' in line:
                findings["shell_spawned"] = True

        if result.returncode in [139, 134]:
            findings["crashed"] = True

        print(f"  [+] Sandbox complete —"
              f" shell:{findings['shell_spawned']}"
              f" network:{len(findings['network_attempts'])}"
              f" crashed:{findings['crashed']}")

    except subprocess.TimeoutExpired:
        findings["executed"]  = True
        findings["timed_out"] = True
        print(f"  [!] Sandbox timed out")
    except Exception as e:
        print(f"  [!] Sandbox error: {e}")

    return findings