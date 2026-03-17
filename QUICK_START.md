# VulnSentinel — Quick Start

## Prerequisites

Make sure these are running before you start:

```bash
# 1. Ollama must be running
pgrep -f "ollama serve" || ollama serve &

# 2. Docker image must exist
docker images | grep vulnsentinel-sandbox
# If missing:
docker build -f Dockerfile.sandbox -t vulnsentinel-sandbox .

# 3. mistral:7b must be pulled
ollama list | grep mistral
# If missing:
ollama pull mistral:7b
```

---

## Start the Agent

```bash
cd ~/vuln-sentinel
python3 agent.py
```

You should see:

```
╔══════════════════════════════════════╗
║         VulnSentinel v1.0            ║
║  Privacy-first vulnerability triage  ║
╚══════════════════════════════════════╝
Watching:   vuln-sentinel/incoming
Threshold:  6/10
Dashboard:  http://127.0.0.1:5000
```

---

## Access the Dashboard

**On the VM directly:**
```
http://127.0.0.1:5000
```

**From your Windows machine (SSH tunnel):**
```bash
ssh -L 5000:127.0.0.1:5000 usertest@YOUR_VM_IP
# then open http://localhost:5000 in your browser
```

---

## Test the Pipeline

### Test 1 — Vulnerable binary (recommended first)

```bash
cp tests/vuln_sample incoming/
```

Expected result:
```
Rules:    7/10  — strcpy, system, /bin/sh
LLM:      8/10  — buffer overflow confirmed
Semgrep:  2 findings
Sandbox:  shell spawned CONFIRMED
Decision: ALERT
```

### Test 2 — Vulnerable source code

```bash
cp tests/vuln_sample.c incoming/
```

Expected result:
```
Rules:    6/10  — strcpy, system
LLM:      7/10  — exploitable input handling
Semgrep:  2 findings
Decision: ALERT or SANDBOX
```

### Test 3 — Run both and watch live

Open two terminals:

```bash
# Terminal 1 — watch the agent output
python3 agent.py

# Terminal 2 — drop files
cp tests/vuln_sample incoming/
sleep 60
cp tests/vuln_sample.c incoming/
```

---

## View Reports

### On the dashboard
```
http://127.0.0.1:5000
```
Click "Analysis" in the sidebar. Each card shows filename, risk score, verdict, and signal breakdown.

### From the terminal

```bash
# List all reports
ls -lht reports/

# View the latest report
ls -t reports/*_report.json | head -1 | xargs python3 -m json.tool | head -80
```

### Download JSON
Click "export json" on any card in the dashboard.

---

## Use the AI Chat

1. Open the dashboard
2. Click "AI Chat" in the sidebar
3. Ask anything security-related:

```
what is a buffer overflow and how does strcpy cause it?
explain CVE-2021-44228
what does shell_spawned mean in my sandbox report?
```

Responses stream token by token from your local mistral:7b — nothing leaves the VM.

---

## Generate More Test Files

Use the attack generator (requires Anthropic API key):

```bash
# List available scenarios
python3 tests/attack_generator.py --list

# Generate a specific type
python3 tests/attack_generator.py --scenario stack_overflow
python3 tests/attack_generator.py --scenario command_injection
python3 tests/attack_generator.py --scenario backdoor

# Generate all 10 types
python3 tests/attack_generator.py
```

Generated files land directly in `incoming/` and are analyzed automatically.

---

## Pipeline Timing

| Step              | Time          |
|-------------------|---------------|
| File detection    | ~1 second     |
| Static analysis   | ~2–5 seconds  |
| Ghidra decompile  | ~60 seconds   |
| First vote        | instant       |
| Docker sandbox    | ~30 seconds   |
| LLM analysis      | ~20 seconds   |
| Total (no Ghidra) | ~30–60 sec    |
| Total (+ Ghidra)  | ~90–120 sec   |

---

## Troubleshooting

**File analyzed but no report appears on dashboard**
```bash
ls reports/   # check report was saved
# then refresh the dashboard
```

**Agent not picking up files**
```bash
# Check it's running
ps aux | grep agent.py
# Check incoming/ directory
ls -la incoming/
```

**LLM timed out**
```bash
# Check Ollama is running and model is loaded
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

**Sandbox not running**
```bash
# Check Docker is running
docker ps
# Rebuild image if needed
docker build -f Dockerfile.sandbox -t vulnsentinel-sandbox .
```

**Download JSON button gives error**
```bash
# Make sure dashboard/app.py has: import config
head -10 dashboard/app.py | grep "import config"
```

---

## What Each Directory Does

| Directory    | Purpose                                      |
|-------------|----------------------------------------------|
| `incoming/`  | Drop files here — agent watches this folder  |
| `processed/` | Files moved here after analysis completes    |
| `reports/`   | JSON reports for every analyzed file         |
| `logs/`      | Application logs                             |
| `tests/`     | Sample vulnerable files for testing          |

---

**Version:** 1.0 | **Status:** Phase 1 Complete