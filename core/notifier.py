import requests
import config


def send_slack(filename, llm_result, report_path, sandbox_findings=None):
    score   = llm_result.get("risk_score", 0)
    level   = llm_result.get("risk_level", "unknown").upper()
    summary = llm_result.get("summary", "No summary.")
    verdict = llm_result.get("verdict", "")
    vulns   = llm_result.get("confirmed_vulnerabilities", [])
    actions = llm_result.get("recommended_actions", [])

    emoji = {
        "LOW":      "🟡",
        "MEDIUM":   "🟠",
        "HIGH":     "🔴",
        "CRITICAL": "🚨"
    }.get(level, "⚪")

    vuln_text = ""
    for v in vulns:
        vuln_text += (
            f"• *{v.get('type','?')}* "
            f"at `{v.get('location','unknown')}` "
            f"— {v.get('severity','?').upper()}\n"
            f"  _{v.get('explanation','')}_\n"
        )
    if not vuln_text:
        vuln_text = "_None confirmed_"

    actions_text = "\n".join(f"• {a}" for a in actions) or "_None_"

    if sandbox_findings:
        sb           = sandbox_findings
        sandbox_text = (
            f"• Executed:         "
            f"{'✅' if sb.get('executed') else '❌'}\n"
            f"• Shell spawned:    "
            f"{'🚨 YES' if sb.get('shell_spawned') else '✅ No'}\n"
            f"• Network attempts: "
            f"{len(sb.get('network_attempts', []))}\n"
            f"• File operations:  "
            f"{len(sb.get('file_operations', []))}\n"
            f"• Crashed:          "
            f"{'💥 YES' if sb.get('crashed') else '✅ No'}"
        )
    else:
        sandbox_text = "_Not executed_"

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} VulnSentinel Alert — {filename}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Risk Level:*\n{emoji} {level}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Risk Score:*\n{score}/10"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Verdict:*\n{verdict}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{summary}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Confirmed Vulnerabilities:*\n{vuln_text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Sandbox Behavior:*\n{sandbox_text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recommended Actions:*\n{actions_text}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📄 Report: `{report_path}`"
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(config.SLACK_WEBHOOK, json=payload)
        if response.status_code == 200:
            print(f"  [+] Slack notification sent!")
        else:
            print(f"  [!] Slack failed: {response.text}")
    except Exception as e:
        print(f"  [!] Slack error: {e}")