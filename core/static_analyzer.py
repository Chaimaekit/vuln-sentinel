import subprocess
import os
import json
import config


def run_semgrep(filepath):
    print(f"    [*] Running Semgrep...")
    result = subprocess.getoutput(
        f"semgrep --config=auto --json {filepath} 2>/dev/null"
    )
    try:
        data     = json.loads(result)
        findings = data.get("results", [])
        print(f"    [*] Semgrep: {len(findings)} findings")
        return findings
    except json.JSONDecodeError:
        print(f"    [!] Semgrep returned no valid JSON")
        return []


def run_basic_binary_checks(filepath):
    print(f"    [*] Running binary checks...")
    return {
        "file_info": subprocess.getoutput(
            f"file {filepath}"
        ),
        "checksec": subprocess.getoutput(
            f"checksec --file={filepath} 2>/dev/null"
        ),
        "dangerous_functions": subprocess.getoutput(
            f"objdump -d {filepath} 2>/dev/null | "
            f"grep -E 'strcpy|gets|system|sprintf|scanf|exec'"
        ),
        "interesting_strings": subprocess.getoutput(
            f"strings {filepath} | "
            f"grep -iE '/bin/sh|exec|system|pass|admin|token|http|root'"
        ),
        "suid_check": subprocess.getoutput(
            f"ls -la {filepath}"
        )
    }


def decompile_with_ghidra(filepath):
    print(f"    [*] Decompiling with Ghidra (this takes ~1 min)...")
    filename   = os.path.basename(filepath)
    output_dir = f"/tmp/ghidra_out_{filename}"
    output_file = f"{output_dir}/{filename}_decompiled.c"
    os.makedirs(output_dir, exist_ok=True)

    try:
        result = subprocess.run([
            config.GHIDRA_PATH,
            config.GHIDRA_PROJECT,
            "TempProject",
            "-import", filepath,
            "-postScript", "ExportDecompiled.java",
            "-scriptPath", config.GHIDRA_SCRIPTS,
            "-deleteProject"
        ], capture_output=True, text=True, timeout=180)

        if "ERROR" in result.stderr:
            print(f"    [!] Ghidra error: {result.stderr[-500:]}")

        if os.path.exists(output_file):
            with open(output_file) as f:
                content = f.read()
            print(f"    [*] Ghidra decompile successful")
            return content
        else:
            print(f"    [!] Ghidra ran but output file not found")
            print(f"    [!] Expected: {output_file}")

    except subprocess.TimeoutExpired:
        print(f"    [!] Ghidra timed out (180s)")
    except Exception as e:
        print(f"    [!] Ghidra exception: {e}")

    print(f"    [*] Falling back to objdump")
    return subprocess.getoutput(
        f"objdump -d {filepath} 2>/dev/null | head -300"
    )


def analyze_source(filepath):
    print(f"  [*] Analyzing source code: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source_content = f.read()
    except Exception as e:
        print(f"    [!] Could not read source: {e}")
        source_content = ""
    
    findings = {
        "type":             "source",
        "source_content":   source_content,
        "semgrep_findings": run_semgrep(filepath)
    }
    return findings


def analyze_binary(filepath):
    print(f"  [*] Analyzing binary: {filepath}")

    findings = {
        "type":          "binary",
        "basic_checks":  run_basic_binary_checks(filepath),
    }

    decompiled = decompile_with_ghidra(filepath)
    if decompiled:
        temp_c = f"/tmp/{os.path.basename(filepath)}_decompiled.c"
        with open(temp_c, "w") as f:
            f.write(decompiled)

        findings["decompiled_snippet"] = decompiled[:3000]
        findings["semgrep_on_decompiled"] = run_semgrep(temp_c)

    return findings