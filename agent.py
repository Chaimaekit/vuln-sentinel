import os
import time
import threading
import shutil
from watchdog.observers import Observer
from watchdog.events    import FileSystemEventHandler
import config
from core.file_router     import is_binary, is_analyzable
from core.static_analyzer import analyze_source, analyze_binary
from core.llm_analyzer    import analyze_with_llm
from core.rules_engine    import score_by_rules, semgrep_count, should_call_llm, vote
from core.sandbox         import run_in_sandbox
from core.report          import save_report
from core.notifier        import send_slack
from dashboard.app        import start_dashboard

#new dir to avoid reanalyzing files
PROCESSED_DIR = os.path.join(config.BASE_DIR, "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)



def process_file(filepath):
    filename = os.path.basename(filepath)
    print(f"\n{'='*55}")
    print(f"[*] New file: {filename}")

    if not is_analyzable(filepath):
        print(f"  [!] Skipping — not an analyzable file type")
        return

    # ── Step 1: Static analysis ──────────────────────────
    binary   = is_binary(filepath)
    findings = analyze_binary(filepath) if binary \
               else analyze_source(filepath)

    # ── Step 2: Signal 1 — Rules engine (deterministic) ──
    rule_score, rule_reasons = score_by_rules(findings)
    sem_count                = semgrep_count(findings)
    print(f"  [*] Rules score: {rule_score}/10")
    for r in rule_reasons:
        print(f"      → {r}")

    # ── Step 3: Signal 2 — LLM (only if rules flagged) ───
    if should_call_llm(rule_score):
        llm_result = analyze_with_llm(findings, filename)
        llm_score  = llm_result.get("risk_score", 0)
    else:
        print(f"  [*] Rules: clean — skipping LLM")
        llm_score  = 0
        llm_result = {
            "risk_score":                0,
            "confidence":                9,
            "risk_level":                "low",
            "verdict":                   "Clean — no signals from rules engine",
            "confirmed_vulnerabilities": [],
            "recommended_actions":       ["No action required"],
            "summary":                   f"Rules engine found no risk signals. Score: {rule_score}/10"
        }

    # ── Step 4: First vote (no sandbox data yet) ─────────
    verdict = vote(rule_score, llm_score, sem_count)
    print(f"  [*] Vote 1: {verdict['decision'].upper()} "
          f"({verdict['confidence']}) → {verdict['action']}")
    for s in verdict["signals"]:
        print(f"      · {s}")

    # ── Step 5: Sandbox if vote says so ──────────────────
    sandbox_findings = None

    if verdict["action"] == "SANDBOX":
        print(f"  [!] Sandboxing for behavioral confirmation...")
        sandbox_findings = run_in_sandbox(filepath)

        # ── Step 6: Signal 4 added — re-vote ─────────────
        verdict = vote(rule_score, llm_score, sem_count, sandbox_findings)
        print(f"  [*] Vote 2: {verdict['decision'].upper()} "
              f"({verdict['confidence']}) → {verdict['action']}")
        for s in verdict["signals"]:
            print(f"      · {s}")

        # LLM second pass with behavioral context
        combined   = {**findings, "sandbox": sandbox_findings}
        llm_result = analyze_with_llm(combined, filename)
        llm_score  = llm_result.get("risk_score", 0)

        # Final vote with updated LLM score
        verdict = vote(rule_score, llm_score, sem_count, sandbox_findings)

    # ── Step 7: Save report always ────────────────────────
    report_path = save_report(
        filename, findings, sandbox_findings, llm_result,
        verdict     = verdict,
        rule_score  = rule_score,
        rule_reasons = rule_reasons,
        sem_count   = sem_count
    )
    print(f"  [+] Report saved: {report_path}")

    # ── Step 8: Act on final verdict ─────────────────────
    action = verdict["action"]

    if action == "ALERT":
        print(f"  [!!!] THREAT CONFIRMED — sending alert")
        send_slack(filename, llm_result, report_path, sandbox_findings)

    elif action == "HUMAN_REVIEW":
        print(f"  [⚠]  UNCERTAIN — flagged for human review")
        # Slack soft alert — you can add send_slack_review() later

    elif action == "ARCHIVE":
        print(f"  [✓]  CLEAN — all signals agree, logging only")

    else:
        print(f"  [*]  Action: {action} — logged")

    # ── Step 9: Move file to processed directory ────────
    try:
        processed_path = os.path.join(PROCESSED_DIR, filename)
        shutil.move(filepath, processed_path)
        print(f"  [+] File moved to: processed/{filename}")
    except Exception as e:
        print(f"  [!] Could not move file to processed/: {e}")
        # Try to delete it from incoming to prevent re-analysis
        try:
            os.remove(filepath)
            print(f"  [+] File deleted from incoming/")
        except:
            pass


class FileHandler(FileSystemEventHandler):
    def __init__(self):
        self._seen = {}
        self._lock = threading.Lock()

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._handle(event.src_path)

    def _handle(self, filepath):
        with self._lock:
            last = self._seen.get(filepath, 0)
            now  = time.time()
            if now - last < 30:
                return
            self._seen[filepath] = now

        filename = os.path.basename(filepath)
        if os.path.exists(os.path.join(PROCESSED_DIR, filename)):
            print(f"[*] Skipping {filename} — already processed")
            return

        time.sleep(1) 
        process_file(filepath)


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
