# 🚀 VulnSentinel - Quick Start & Testing Reference

## ✅ System Status: READY FOR TESTING

All safety isolation verified ✓

```
✓ Docker Sandbox       : vulnsentinel-sandbox (ready)
✓ Ollama LLM          : running on localhost:11434
✓ VulnSentinel Agent  : running (monitoring incoming/)
✓ Dashboard           : http://127.0.0.1:5000
✓ Network Isolation   : ✓ PASS (sandbox blocked from internet)
✓ User Privilege      : ✓ PASS (running as non-root)
✓ Memory Limits       : ✓ PASS (512MB enforced)
✓ Auto-Cleanup        : ✓ PASS (containers destroyed)
```

---

## 📁 Test Files Available

All in `vuln-sentinel/tests/`

| File | Type | Expected Risk |
|------|------|---|
| `clean_program` | Binary | 🟢 LOW (1-3) |
| `buffer_overflow.c` | Source | 🔴 HIGH (8-10) |
| `sql_injection.py` | Source | 🔴 HIGH (7-9) |
| `command_injection.js` | Source | 🔴 HIGH (7-9) |
| `hidden_malware.sh` | Script | 🔴 CRITICAL (9-10) |

---

## 🎯 Start Testing - Copy & Paste Commands

### Option A: Test ONE file (recommended first)

```bash
# Terminal 1: Watch real-time analysis
tail -f /tmp/vulnsentinel.log

# Terminal 2: Copy test file
cp vuln-sentinel/tests/buffer_overflow.c \
   vuln-sentinel/incoming/

# Wait ~10 seconds, watch Terminal 1 for analysis
```

### Option B: Test multiple files

```bash
cd vuln-sentinel

# Test clean file
cp tests/clean_program incoming/test1.bin
sleep 8

# Test vulnerability
cp tests/buffer_overflow.c incoming/test2.c
sleep 8

# Test malware
cp tests/hidden_malware.sh incoming/test3.sh
sleep 8
```

### Option C: Test all files

```bash
for f in vuln-sentinel/tests/*; do
  [ -f "$f" ] && cp "$f" vuln-sentinel/incoming/
done
```

---

## 📊 View Results - Choose ONE

### Method 1: Live Terminal Logs
```bash
tail -f /tmp/vulnsentinel.log
```
**Best for:** Understanding the pipeline in real-time

### Method 2: Reports Directory
```bash
ls -lh vuln-sentinel/reports/
```
**Best for:** Seeing all analysis results

### Method 3: View Latest Report
```bash
ls -t vuln-sentinel/reports/*_report.json | head -1 | \
  xargs cat | python3 -m json.tool | head -60
```
**Best for:** Detailed JSON analysis

### Method 4: Web Dashboard
```
http://127.0.0.1:5000
```
**Best for:** Visual overview of all files

---

## 🔍 What You'll See During Analysis

```
[NEW FILE DETECTED]
  ↓
[STATIC ANALYSIS] → Rules Engine, Semgrep, Checksec
  ↓
[FIRST VOTE] → Risk assessment
  ↓
[IF SUSPICIOUS: SANDBOX] → Docker container spawns
  ↓
[STRACE MONITORING] → Capture system calls
  ↓
[LLM ANALYSIS] → AI verdict
  ↓
[FINAL VOTE] → Generate report
  ↓
[ALERT IF THREAT] → Slack notification, report saved
```

---

## 🛡️ Why Your Machine is Safe

### Multi-Layer Isolation

1. **Docker Container** - Complete OS-level isolation
   - Only malware executes there
   - Host system untouched

2. **Network Isolation** - `--network none`
   - Sandbox cannot reach internet
   - Cannot exfiltrate data

3. **Resource Limits** - Memory & CPU capped
   - DoS attacks blocked
   - System remains responsive

4. **User Privilege** - Running as `sandboxuser`
   - Cannot escalate privileges
   - Cannot access sensitive files

5. **Auto-Cleanup** - Container destroyed after
   - Zero persistence
   - No traces left behind

6. **File Permissions** - Read-only mounts
   - Sandbox cannot modify incoming files
   - Cannot write to host filesystem

---

## 📈 Expected Test Results

### ✅ Clean Program
```
Rules:      0/10 (clean)
LLM:        "No vulnerabilities"
Semgrep:    0 findings
Sandbox:    Clean execution
Decision:   ARCHIVE (safe)
Risk:       🟢 1-2
```

### 🔴 Buffer Overflow  
```
Rules:      6/10 (gets + strcpy)
LLM:        "Exploitable buffer overflow"
Semgrep:    2 findings
Sandbox:    Crash detected, shell spawned
Decision:   ALERT (threat)
Risk:       🔴 8-10
```

### 🔴 SQL Injection
```
Rules:      3/10 (input patterns)
LLM:        "Direct SQL concatenation"
Semgrep:    4 findings
Sandbox:    N/A (script analysis)
Decision:   ALERT (threat)
Risk:       🔴 7-9
```

### 🔴 Malware
```
Rules:      7/10 (/bin/sh, shell spawning)
LLM:        "Reverse shell trojan"
Semgrep:    5+ findings
Sandbox:    Network connect blocked, shell spawned
Decision:   ALERT (threat)
Risk:       🔴 9-10
```

---

## ⏱️ Timeline

- **Detection**: ~1 second (file appears in incoming/)
- **Static Analysis**: ~2 seconds (rules, semgrep)
- **First Vote**: ~1 second (decision to sandbox?)
- **Sandbox Execution**: ~30 seconds (if needed)
- **LLM Analysis**: ~10-30 seconds (AI verdict)
- **Final Report**: ~2 seconds (save to disk)
- **Total**: ~30-60 seconds per file

---

## 🚨 Troubleshooting Quick Fixes

### Agent not analyzing files?
```bash
ps aux | grep python.*agent.py
# If dead, restart:
cd vuln-sentinel && python3 agent.py &
```

### No reports being generated?
```bash
# Check permissions
ls -la vuln-sentinel/reports/
chmod 777 vuln-sentinel/reports/
```

### Ollama connection failing?
```bash
# Check if running
pgrep -f "ollama serve"
# If not running:
ollama serve &
```

### Docker image missing?
```bash
cd vuln-sentinel && \
  docker build -f Dockerfile.sandbox -t vulnsentinel-sandbox .
```

---

## 📚 For More Details

- **README.md** - Full documentation and setup
- **HOW_IT_WORKS.md** - Deep technical explanation
- **TESTING_GUIDE.md** - Comprehensive testing walkthrough
- **test_and_verify.sh** - System verification script

---

## 🎓 Learning Path

1. **First**: Test `clean_program` to verify system works
2. **Then**: Test `buffer_overflow.c` to see detection in action
3. **Then**: Test `sql_injection.py` to see LLM analysis
4. **Finally**: Test `hidden_malware.sh` to see full pipeline including sandbox

Each test will teach you something about the system!

---

**Status**: ✅ Ready | **Safety**: ✅ Verified | **Time**: 🚀 Ready to go!
