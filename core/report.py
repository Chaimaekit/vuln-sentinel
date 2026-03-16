import json
import os
import time
import config


def save_report(filename, static_findings, sandbox_findings,
                llm_result, verdict=None, rule_score=0,
                rule_reasons=None, sem_count=0):

    sandbox_threat = False
    if sandbox_findings:
        sandbox_threat = (
            sandbox_findings.get("shell_spawned", False) or
            len(sandbox_findings.get("network_attempts", [])) > 0 or
            sandbox_findings.get("crashed", False)
        )

    safe_name   = filename.replace("/", "_").replace(" ", "_")
    report_name = f"{safe_name}_{int(time.time())}_report.json"
    report_path = os.path.join(config.REPORTS_DIR, report_name)

    report = {
        "filename":    filename,
        "report_file": report_name,        
        "timestamp":   time.strftime("%Y-%m-%d %H:%M:%S"),
        "risk_score":  llm_result.get("risk_score", 0),
        "risk_level":  llm_result.get("risk_level", "unknown"),
        "verdict":     llm_result.get("verdict", ""),

        "signal_scores": {
            "rules_score":    rule_score,
            "rules_reasons":  rule_reasons or [],
            "llm_score":      llm_result.get("risk_score", 0),
            "llm_confidence": llm_result.get("confidence", 0),
            "semgrep_count":  sem_count,
            "sandbox_ran":    sandbox_findings is not None,
            "sandbox_threat": sandbox_threat,
        },

        "decision": verdict if verdict else {
            "final_action": "UNKNOWN",
            "confidence":   "unknown",
            "votes":        {},
            "signals":      []
        },

        "static_findings":  static_findings,
        "sandbox_findings": sandbox_findings,
        "llm_analysis":     llm_result,
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report_path


def load_all_reports():
    reports = []
    for fname in os.listdir(config.REPORTS_DIR):
        if fname.endswith("_report.json"):
            path = os.path.join(config.REPORTS_DIR, fname)
            try:
                with open(path) as f:
                    data = json.load(f)
                    if "report_file" not in data:
                        data["report_file"] = fname
                    reports.append(data)
            except Exception:
                pass

    reports.sort(
        key=lambda x: x.get("risk_score", 0), reverse=True
    )
    return reports
