import config
import re

def strip_comments(source_code):
    result = []
    i = 0
    in_string = False
    string_char = None
    
    while i < len(source_code):
        if source_code[i] in ('"', "'") and (i == 0 or source_code[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = source_code[i]
            elif source_code[i] == string_char:
                in_string = False
            result.append(source_code[i])
            i += 1
        elif in_string:
            result.append(source_code[i])
            i += 1
        elif i < len(source_code) - 1 and source_code[i:i+2] == '//':
            while i < len(source_code) and source_code[i] != '\n':
                i += 1
            if i < len(source_code):
                result.append('\n')
                i += 1
        elif i < len(source_code) - 1 and source_code[i:i+2] == '/*':
            i += 2
            while i < len(source_code) - 1:
                if source_code[i:i+2] == '*/':
                    i += 2
                    break
                if source_code[i] == '\n':
                    result.append('\n')
                i += 1
        elif source_code[i] == '#':
            while i < len(source_code) and source_code[i] != '\n':
                i += 1
            if i < len(source_code):
                result.append('\n')
                i += 1
        else:
            result.append(source_code[i])
            i += 1
    
    return ''.join(result)

RULES = {
    "gets":        {"score": 4, "reason": "gets() — no input limit"},
    "strcpy":      {"score": 3, "reason": "strcpy() — no bounds check"},
    "sprintf":     {"score": 2, "reason": "sprintf() — can overflow"},
    "system":      {"score": 3, "reason": "system() — executes shell"},
    "scanf":       {"score": 2, "reason": "scanf() — can overflow"},
    "exec":        {"score": 3, "reason": "exec() — executes commands"},
    "/bin/sh":     {"score": 3, "reason": "/bin/sh string present"},
    "/bin/bash":   {"score": 3, "reason": "/bin/bash string present"},
    "password":    {"score": 2, "reason": "hardcoded password string"},
    "token":       {"score": 2, "reason": "hardcoded token string"},
    "No canary":   {"score": 2, "reason": "no stack canary"},
    "No PIE":      {"score": 1, "reason": "no PIE — static addresses"},
    "NX disabled": {"score": 2, "reason": "stack is executable"},
}

SEMGREP_SEVERITY = {
    "ERROR":   4,
    "WARNING": 2,
    "INFO":    1,
}


def score_by_rules(findings):
    score   = 0
    reasons = []
    file_type = findings.get("type", "unknown")

    if file_type == "binary":
        basic    = findings.get("basic_checks", {})
        danger   = basic.get("dangerous_functions", "")
        strings  = basic.get("interesting_strings",  "")
        checksec = basic.get("checksec",              "")

        for keyword, rule in RULES.items():
            if keyword in danger or \
               keyword in strings or \
               keyword in checksec:
                score   += rule["score"]
                reasons.append(rule["reason"])

    elif file_type == "source":
        source_content = findings.get("source_content", "")
        
        cleaned_content = strip_comments(source_content)
        dangerous_patterns = {
            r'\bgets\s*\(': {"score": 4, "reason": "gets() — no input limit"},
            r'\bstrcpy\s*\(': {"score": 3, "reason": "strcpy() — no bounds check"},
            r'\bstrcat\s*\(': {"score": 2, "reason": "strcat() — no bounds check"},
            r'\bsprintf\s*\(': {"score": 2, "reason": "sprintf() — can overflow"},
            r'\bscanf\s*\(': {"score": 2, "reason": "scanf() — can overflow"},
            r'\bsystem\s*\(': {"score": 3, "reason": "system() — executes shell"},
            r'\bexecve?\s*\(': {"score": 3, "reason": "exec() — executes commands"},
            r'\beval\s*\(': {"score": 3, "reason": "eval() — code injection risk"},
            r'os\.system\s*\(': {"score": 3, "reason": "os.system() — shell execution"},
            r'subprocess\.call\s*\(': {"score": 2, "reason": "subprocess without shell=False"},
        }
        
        pattern_found = set()
        for pattern, rule in dangerous_patterns.items():
            try:
                matches = re.finditer(pattern, cleaned_content)
                count = len(list(matches))
                if count > 0:
                    pattern_found.add(pattern)
                    if count > 1:
                        score += rule["score"] + 1
                        reasons.append(f"{rule['reason']} (found {count} times)")
                    else:
                        score += rule["score"]
                        reasons.append(rule["reason"])
            except re.error:
                pass
        
        for finding in findings.get("semgrep_findings", []):
            severity = finding.get("extra", {}).get("severity", "INFO")
            score   += SEMGREP_SEVERITY.get(severity, 1)
            reasons.append(finding.get("check_id", "semgrep rule"))

    return min(score, 10), reasons


def semgrep_count(findings):
    src = findings.get("semgrep_findings") or \
          findings.get("semgrep_on_decompiled") or []
    return len(src)


def should_call_llm(rule_score, sem_count=0):
    return rule_score >= 2 or sem_count >= 2


def vote(rule_score, llm_score, sem_count, sandbox_findings=None):
    votes   = []
    signals = []

    # Signal 1 — Rules engine (deterministic)
    if rule_score >= 6:
        votes.append("threat");     signals.append(f"Rules: {rule_score}/10 HIGH")
    elif rule_score >= 3:
        votes.append("suspicious"); signals.append(f"Rules: {rule_score}/10 MEDIUM")
    else:
        votes.append("clean");      signals.append(f"Rules: {rule_score}/10 LOW")

    # Signal 2 — LLM (can hallucinate — just one vote)
    if llm_score >= 7:
        votes.append("threat");     signals.append(f"LLM: {llm_score}/10 HIGH")
    elif llm_score >= 4:
        votes.append("suspicious"); signals.append(f"LLM: {llm_score}/10 MEDIUM")
    else:
        votes.append("clean");      signals.append(f"LLM: {llm_score}/10 LOW")

    # Signal 3 — Semgrep count (deterministic)
    if sem_count >= 3:
        votes.append("threat");     signals.append(f"Semgrep: {sem_count} findings HIGH")
    elif sem_count >= 1:
        votes.append("suspicious"); signals.append(f"Semgrep: {sem_count} findings MEDIUM")
    else:
        votes.append("clean");      signals.append(f"Semgrep: {sem_count} findings LOW")

    # Signal 4 — Sandbox ground truth (only if available)
    if sandbox_findings:
        file_ops  = sandbox_findings.get("file_operations", [])
        sensitive = any(
            p in f for f in file_ops
            for p in ["/etc/passwd", "/etc/shadow", "/.ssh"]
        )
        sb_threat = (
            sandbox_findings.get("shell_spawned", False) or
            len(sandbox_findings.get("network_attempts", [])) > 0 or
            sandbox_findings.get("crashed", False)
        )
        if sb_threat:
            votes.append("threat");     signals.append("Sandbox: malicious behavior CONFIRMED")
        elif sensitive:
            votes.append("suspicious"); signals.append("Sandbox: sensitive file access detected")
        else:
            votes.append("clean");      signals.append("Sandbox: no malicious behavior")

    threat_votes     = votes.count("threat")
    suspicious_votes = votes.count("suspicious")
    clean_votes      = votes.count("clean")
    total            = len(votes)

    # Decision requires MAJORITY
    if threat_votes >= 2:
        decision   = "threat"
        confidence = "high" if threat_votes >= 3 else "medium"
    elif clean_votes == total:
        decision   = "clean"
        confidence = "high"
    elif suspicious_votes >= 1 or threat_votes == 1:
        decision   = "suspicious"
        confidence = "low"
    else:
        decision   = "suspicious"
        confidence = "low"

    # Action based on decision + whether sandbox ran
    sandbox_done = sandbox_findings is not None
    if decision == "threat" and sandbox_done:
        action = "ALERT"
    elif decision == "threat" and not sandbox_done:
        action = "SANDBOX"
    elif decision == "suspicious" and not sandbox_done:
        action = "SANDBOX"
    elif decision == "suspicious" and sandbox_done:
        action = "HUMAN_REVIEW"
    elif decision == "clean" and confidence == "high":
        action = "ARCHIVE"
    else:
        action = "HUMAN_REVIEW"

    return {
        "decision":   decision,
        "confidence": confidence,
        "action":     action,
        "signals":    signals,
        "votes": {
            "threat":     threat_votes,
            "suspicious": suspicious_votes,
            "clean":      clean_votes,
        }
    }
