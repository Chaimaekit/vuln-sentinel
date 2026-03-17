# VulnSentinel

> Privacy-first vulnerability triage and security analysis platform

A real-time vulnerability detection and analysis system that combines static analysis, local AI, and behavioral sandboxing to identify and classify security threats in both source code and compiled binaries. Everything runs on-premise — no data ever leaves your machine.

---

## Overview

VulnSentinel is an **automated security triage system** that analyzes files (source code, binaries, scripts) and determines if they contain vulnerabilities. It uses a multi-signal approach combining deterministic rules, AI-powered analysis, and dynamic behavioral inspection to minimize false positives and provide high-confidence threat assessments.

### Key Features

- **4-Signal Voting System** — Rules engine, LLM, Semgrep, and sandbox each cast an independent vote
- **Source and Binary Analysis** — handles `.c`, `.cpp`, `.py`, `.js`, `.java`, `.go`, ELF binaries, and more
- **Local LLM** — uses Ollama with Mistral 7b, runs entirely on CPU, no GPU required
- **Docker Sandbox** — behavioral analysis in an isolated container with no network access
- **Real-time Monitoring** — watchdog detects files the moment they land in `incoming/`
- **Web Dashboard** — dark-themed UI with signal scores, voting breakdown, and AI chat
- **Slack Alerts** — instant notification on confirmed threats
- **Privacy-first** — zero external dependencies at analysis time

---

## Architecture

### 4-Signal Pipeline

```
Signal 1: Rules Engine   — deterministic, pattern matching, cannot hallucinate
Signal 2: LLM Analyzer   — context-aware AI, one vote of four, can be overruled
Signal 3: Semgrep        — community security rules, deterministic
Signal 4: Sandbox        — ground truth, actual behavioral execution in Docker
```

Each signal votes `threat / suspicious / clean`. Majority wins.

### Processing Flow

```
incoming/ → quarantine (chmod -x) → file type detection → static analysis
                                                                ↓
                                                    Rules Engine + Semgrep
                                                                ↓
                                                    First vote (3 signals)
                                                                ↓
                                              if suspicious → Docker Sandbox
                                                                ↓
                                                    Second vote (4 signals)
                                                                ↓
                                                  Save report → Alert if threat
```

### Decision Matrix

| Threat Votes | Decision       | Action        |
|-------------|----------------|---------------|
| 3–4 / 4     | CONFIRMED      | ALERT + Slack |
| 2 / 4       | PROBABLE       | ALERT + Slack |
| 1 / 4       | SUSPICIOUS     | HUMAN_REVIEW  |
| 0 / 4       | CLEAN          | ARCHIVE       |

---

## Requirements

- Python 3.10+
- Docker
- Ollama with `mistral:7b` pulled
- Ubuntu 22.04+ (recommended)
- System tools: `semgrep`, `checksec`, `objdump`, `strings`, `file`
- Ghidra 11.1.2 (optional, for binary decompilation)

---

## Installation

### 1. Clone and install Python dependencies

```bash
git clone https://github.com/Chaimaekit/vuln-sentinel.git
cd vuln-sentinel
pip install -r requirements.txt --break-system-packages
```

### 2. Install system tools

```bash
sudo apt-get install -y binutils file
pip install semgrep --break-system-packages
pip install checksec --break-system-packages
```

### 3. Install and start Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral:7b
```

### 4. Build the sandbox Docker image

```bash
docker build -f Dockerfile.sandbox -t vulnsentinel-sandbox .
```

### 5. Configure Slack (optional)

Create a `.env` file in the project root:

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 6. Install Ghidra (optional, for binary decompilation)

```bash
wget https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.1.2_build/ghidra_11.1.2_PUBLIC_linux_x86_64.zip
unzip ghidra_11.1.2_PUBLIC_linux_x86_64.zip -d ~/tools/
```

---

## Usage

### Start the agent

```bash
python3 agent.py
```

The agent will:
- Watch `incoming/` for new files
- Strip execute permissions immediately on arrival
- Run the full 4-signal analysis pipeline
- Save JSON reports to `reports/`
- Send Slack alerts for confirmed threats
- Serve the dashboard at `http://localhost:5000`

### Drop a file for analysis

```bash
cp tests/vuln_sample incoming/
```

### Access the dashboard

```
http://localhost:5000
```

Or via SSH tunnel from your Windows machine:

```bash
ssh -L 5000:127.0.0.1:5000 usertest@YOUR_VM_IP
# then open http://localhost:5000 in your browser
```

---

## Configuration

Edit `config.py` to adjust:

```python
RISK_THRESHOLD  = 6     # minimum score to trigger alert (0–10)
SANDBOX_TIMEOUT = 30    # seconds before sandbox is killed
SANDBOX_MEMORY  = "512m"
SANDBOX_CPUS    = "0.5"
DASHBOARD_PORT  = 5000
```

---

## Directory Structure

```
vuln-sentinel/
├── agent.py                      # main entry point + file watcher
├── config.py                     # all configuration constants
├── cli.py                        # command line interface
├── requirements.txt
├── Dockerfile.sandbox
├── .env                          # secrets (not committed)
├── core/
│   ├── file_router.py            # binary vs source detection
│   ├── static_analyzer.py        # Ghidra + Semgrep + checksec
│   ├── rules_engine.py           # deterministic scoring + voting
│   ├── llm_analyzer.py           # Ollama mistral:7b integration
│   ├── sandbox.py                # Docker isolation + strace
│   ├── report.py                 # JSON report generation
│   └── notifier.py               # Slack webhook alerts
├── dashboard/
│   └── app.py                    # Flask UI + streaming AI chat
├── ghidra_scripts/
│   └── ExportDecompiled.java     # headless decompilation script
├── tests/
│   ├── vuln_sample.c             # test vulnerable C program
│   └── vuln_sample               # compiled binary
├── incoming/                     # drop files here
├── reports/                      # JSON reports output
├── processed/                    # files moved here after analysis
└── logs/
```

---

## Threat Actions

| Action       | Condition                          | Response                        |
|-------------|------------------------------------|---------------------------------|
| ALERT        | 2+ signals vote threat             | Slack notification + JSON report |
| HUMAN_REVIEW | Signals conflict, sandbox unclear  | Flagged for manual inspection   |
| ARCHIVE      | All signals agree: clean           | Report saved, no alert          |

---

## Supported File Types

**Source code:** `.c` `.cpp` `.h` `.py` `.js` `.ts` `.java` `.go` `.rb` `.php` `.cs` `.rs`

**Binaries:** ELF executables, compiled objects, shared libraries `.so`

**Skipped:** images, archives, audio/video, empty files

---

## Security Design

- Files have execute bits stripped immediately on arrival (`chmod -x`)
- Only a copy enters the Docker sandbox — original stays locked
- Sandbox has `--network none`, `--cap-drop ALL`, `--memory 512m`
- Container is destroyed after 30 seconds regardless of outcome
- Ollama runs locally — no data sent externally
- LLM is one vote of four — three deterministic signals prevent hallucination from deciding alone

---

## Troubleshooting

**Ollama not responding**
```bash
pgrep -f "ollama serve" || ollama serve &
```

**Semgrep not found**
```bash
pip install semgrep --break-system-packages
```

**Docker image missing**
```bash
docker build -f Dockerfile.sandbox -t vulnsentinel-sandbox .
```

**Files not being detected**
```bash
# Check agent is running
ps aux | grep agent.py
# Check incoming/ is being watched
ls -la incoming/
```

**Dashboard not loading**
```bash
# Make sure you're accessing via SSH tunnel or directly on the VM
curl http://127.0.0.1:5000
```

---

## Roadmap

### Phase 2 (next)
- Entropy analysis — detect packed/obfuscated binaries before static analysis
- YARA signatures — 5th detection signal
- Bandit (Python) + Flawfinder (C/C++) — better source scanners
- Hardened sandbox — spoof CPU, RAM, username to defeat evasion
- RAG pipeline — ChromaDB + CVEfixes for grounded LLM answers
- PDF report export
- CVSS v3 scoring

### Phase 3
- LoRA fine-tuning on security dataset (Google Colab → local adapter)
- Agent framework — LLM autonomously decides which tools to run

### Phase 4
- Docker image scanning
- PCAP network analysis
- Memory forensics
- CI/CD integration

---

**Version:** 1.0 | **Status:** Phase 1 Complete