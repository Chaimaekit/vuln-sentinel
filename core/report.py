import json
import os
import time
import config


def save_report(filename, static_findings, sandbox_findings, llm_result):
    """
    Saves complete analysis report to JSON file.
    """
    report = {
        "filename":        filename,
        "timestamp":       time.strftime("%Y-%m-%d %H:%M:%S"),
        "risk_score":      llm_result.get("risk_score", 0),
        "risk_level":      llm_result.get("risk_level", "unknown"),
        "verdict":         llm_result.get("verdict", ""),
        "static_findings": static_findings,
        "sandbox_findings": sandbox_findings,
        "llm_analysis":    llm_result
    }

    safe_name   = filename.replace("/", "_").replace(" ", "_")
    report_path = os.path.join(
        config.REPORTS_DIR,
        f"{safe_name}_{int(time.time())}_report.json"
    )

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"  [+] Report saved: {report_path}")
    return report_path


def load_all_reports():
    """
    Loads all saved reports for the dashboard.
    Returns list sorted by risk score highest first.
    """
    reports = []
    for filename in os.listdir(config.REPORTS_DIR):
        if filename.endswith("_report.json"):
            path = os.path.join(config.REPORTS_DIR, filename)
            try:
                with open(path) as f:
                    reports.append(json.load(f))
            except Exception:
                pass

    reports.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    return reports