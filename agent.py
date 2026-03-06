import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import config
from core.file_router     import is_binary, is_analyzable
from core.static_analyzer import analyze_source, analyze_binary
from core.llm_analyzer    import analyze_with_llm
from core.sandbox         import run_in_sandbox
from core.report          import save_report
from core.notifier        import send_slack
from dashboard.app        import start_dashboard


def process_file(filepath):
    filename = os.path.basename(filepath)
    print(f"\n{'='*55}")
    print(f"[*] New file: {filename}")

    # Skip unanalyzable files
    if not is_analyzable(filepath):
        print(f"  [!] Skipping — not an analyzable file type")
        return

    # Step 1 — Static analysis
    binary   = is_binary(filepath)
    findings = analyze_binary(filepath) if binary \
               else analyze_source(filepath)

    # Step 2 — LLM first pass
    llm_result      = analyze_with_llm(findings, filename)
    raw_score = llm_result.get("risk_score", 0)
    try:
        score = int(raw_score)
    except (ValueError, TypeError):
        # Map text values to numbers if LLM returns words
        level_map = {"low": 3, "medium": 5, "high": 8, "critical": 10}
        score = level_map.get(str(raw_score).lower(), 0)
    sandbox_findings = None

    # Step 3 — Sandbox if risky enough
    if score >= config.RISK_THRESHOLD:
        print(f"  [!] Risk {score}/10 — isolating in sandbox")
        sandbox_findings = run_in_sandbox(filepath)

        # Step 4 — LLM second pass with behavioral data
        combined   = {**findings, "sandbox": sandbox_findings}
        llm_result = analyze_with_llm(combined, filename)
        score      = llm_result.get("risk_score", 0)

    # Step 5 — Save report always
    report_path = save_report(
        filename, findings, sandbox_findings, llm_result
    )

    # Step 6 — Notify Slack if still risky
    if score >= config.RISK_THRESHOLD:
        send_slack(filename, llm_result, report_path, sandbox_findings)
    else:
        print(f"  [*] Risk {score}/10 — below threshold, logged only")


class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            time.sleep(1)
            process_file(event.src_path)


if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════╗
║         VulnSentinel v1.0            ║
║  Privacy-first vulnerability triage  ║
╚══════════════════════════════════════╝
Watching:   {config.INCOMING_DIR}
Threshold:  {config.RISK_THRESHOLD}/10
Dashboard:  http://{config.DASHBOARD_HOST}:{config.DASHBOARD_PORT}
    """)

    threading.Thread(
        target=start_dashboard, daemon=True
    ).start()
    observer = Observer()
    observer.schedule(
        FileHandler(), config.INCOMING_DIR, recursive=False
    )
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Shutting down VulnSentinel...")
        observer.stop()
    observer.join()