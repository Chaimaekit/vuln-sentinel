# VulnSentinel

> Privacy-first vulnerability triage and security analysis platform

A sophisticated real-time vulnerability detection and analysis system that combines static analysis, machine learning, and behavioral sandboxing to identify and classify security threats in both source code and compiled binaries.

## 🎯 Overview

VulnSentinel is an **automated security triage system** designed to analyze files (source code, binaries, scripts) and determine if they contain vulnerabilities. It uses a multi-layered approach combining deterministic rules, AI-powered analysis, and dynamic behavioral inspection to minimize false positives and provide high-confidence threat assessments.

### Key Features

- **Multi-Signal Analysis**: Combines 4 independent detection methods for high accuracy
- **Source & Binary Analysis**: Handles `.c`, `.cpp`, `.py`, `.js`, `.java`, `.go`, ELF binaries, and more
- **LLM-Powered Analysis**: Uses local Ollama with Mistral models for context-aware vulnerability assessment
- **Behavioral Inspection**: Docker-based sandboxing for safe dynamic analysis
- **Real-time File Monitoring**: Automatic analysis of files as they arrive
- **Rich Reporting**: Structured JSON reports with detailed findings
- **Web Dashboard**: Interactive visual interface for reviewing analysis results
- **Slack Integration**: Instant alerts for high-risk threats
- **Privacy-First**: All analysis runs locally; no external cloud dependencies

## 🏗️ Architecture

### Analysis Pipeline

VulnSentinel uses a 4-signal voting system to make detection decisions:

1. **Rules Engine** (deterministic) - Pattern matching for known vulnerable functions/patterns
2. **LLM Analyzer** (AI-based) - Context-aware analysis using Mistral LLM
3. **Semgrep** (deterministic) - Code pattern analysis with community rules
4. **Sandbox** (behavioral) - Safe dynamic execution analysis in isolated Docker container

Each signal votes on threat level (clean/suspicious/threat), and majority consensus determines the final action.

### File Processing Flow

```
incoming/ → File Detection → Type Classification → Static Analysis
                                                  ↓
                                          Rules Engine Vote
                                                  ↓
                                          (If flagged: LLM Analysis)
                                                  ↓
                                          First Consensus Vote
                                                  ↓
                                    (If suspicious: Docker Sandbox)
                                                  ↓
                                          Second Consensus Vote
                                                  ↓
                                          Save Report + Alert
```

## 📋 Requirements

- Python 3.8+
- Docker (for sandboxing)
- Ollama with Mistral model installed locally
- Linux/macOS (Ubuntu 22.04+ recommended)
- Tools: `semgrep`, `ghidra`, `checksec`, `objdump`, `strings`, `file`

## 🚀 Installation

### 1. Clone and Setup

```bash
git clone <repo-url>
cd vuln-sentinel
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install -y semgrep checksec binutils

# For Ghidra integration:
wget https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.1.2_build/ghidra_11.1.2_PUBLIC_linux_x86_64.zip
unzip ghidra_11.1.2_PUBLIC_linux_x86_64.zip -d ~/tools/
```

### 3. Setup Ollama

```bash
# Install Ollama
ollama pull mistral:7b
```

### 4. Build Sandbox Docker Image

```bash
docker build -f Dockerfile.sandbox -t vulnsentinel-sandbox .
```

### 5. Configure Environment

```bash
# .env file (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Edit [config.py](config.py) to customize:
- Directory paths (incoming, reports, logs)
- Risk threshold (0-10)
- Sandbox resources (memory, CPU)
- Dashboard host/port

## 🎮 Usage

### Start Real-time Monitoring

```bash
# Watch the incoming/ directory and process files automatically
python agent.py
```

The system will:
- Monitor `incoming/` directory for new files
- Automatically analyze each file through the full pipeline
- Save detailed reports to `reports/`
- Send Slack alerts for threats (if configured)
- Display results on the web dashboard

### Access the Dashboard

Once running, open your browser:
```
http://localhost:5000
```

View:
- All analyzed files and risk scores
- Detailed findings per file
- Risk distribution charts
- LLM analysis verdicts
- Sandbox behavioral reports

### Manual File Analysis

```bash
# Place files in the incoming directory
cp vulnerable_binary incoming/
cp source_code.c incoming/

# System automatically detects and analyzes them
# Check reports/ for generated JSON reports
```


## 🔧 Configuration

### Risk Threshold

Adjust in [config.py](config.py):

```python
RISK_THRESHOLD  = 6    # 0-10 scale
SANDBOX_TIMEOUT = 30   # seconds
```

### Slack Notifications

Threats with score ≥ RISK_THRESHOLD trigger Slack alerts. Get webhook URL:
1. Create Slack App: https://api.slack.com/apps
2. Add Incoming Webhook
3. Set `SLACK_WEBHOOK_URL` in `.env`

### Gemidra Path

Update path to your Ghidra installation:

```python
GHIDRA_PATH = os.path.expanduser("~/tools/ghidra_11.1.2_PUBLIC/support/analyzeHeadless")
```

## 📁 Directory Structure

```
vuln-sentinel/
  ├── agent.py                    # Main orchestration (+file watching)
  ├── config.py                   # Configuration constants
  ├── cli.py                      # CLI interface (optional)
  ├── core/
  │   ├── file_router.py          # File type detection
  │   ├── static_analyzer.py      # Semgrep, binary analysis, Ghidra
  │   ├── rules_engine.py         # Rule-based scoring
  │   ├── llm_analyzer.py         # Ollama integration
  │   ├── sandbox.py              # Docker sandbox execution
  │   ├── report.py               # Report generation
  │   └── notifier.py             # Slack notifications
  ├── dashboard/
  │   └── app.py                  # Flask web dashboard
  ├── ghidra_scripts/
  │   └── ExportDecompiled.java   # Ghidra decompilation script
  ├── incoming/                   # Drop files here for analysis
  ├── reports/                    # Generated JSON reports
  ├── logs/                       # Application logs
  └── Dockerfile.sandbox          # Sandbox container definition
```

## 🛡️ Threat Actions

The system can trigger three actions:

| Action | Condition | Response |
|--------|-----------|----------|
| **ALERT** | Multiple signals agree on threat | Slack notification, report generated |
| **HUMAN_REVIEW** | Signals conflict / uncertain | Logged for manual inspection |
| **ARCHIVE** | All signals agree: clean | Report only, no alert |

## 📚 Supported File Types

### Source Code
- `.c`, `.cpp`, `.h` (C/C++)
- `.py` (Python)
- `.js`, `.ts` (JavaScript/TypeScript)
- `.java` (Java)
- `.go` (Go)
- `.rb` (Ruby)
- `.php` (PHP)
- `.cs` (C#)
- `.rs` (Rust)

### Binaries
- ELF executables (Linux)
- Compiled objects
- Shared libraries (`.so`)

### Skipped
- Images, archives, audio/video files
- Empty files

## 🔒 Security Considerations

- **Sandboxing**: High-risk files execute in isolated Docker without network access
- **Local Processing**: No data sent to external services (Ollama runs locally)
- **Permissions**: Sandbox runs as unprivileged user
- **Resource Limits**: CPU/memory quotas prevent DoS

## 🐛 Troubleshooting

### Ollama Not Responding
```bash
# Check Ollama is running
curl http://localhost:11434/api/generate

# Restart Ollama
ollama serve
```

### Semgrep Not Found
```bash
pip install semgrep
# or
brew install semgrep
```

### Docker Sandbox Issues
```bash
# Rebuild image
docker build -f Dockerfile.sandbox -t vulnsentinel-sandbox .

# Check image exists
docker images | grep vulnsentinel-sandbox
```

### Files Not Detected
- Ensure files are placed in `incoming/` directory
- Check file permissions (should be readable)
- System ignores files <1 second old (debounce window)

## 📝 Logs

Application logs appear in `logs/` directory and on console. Increase verbosity by modifying print statements in [agent.py](agent.py).

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Additional SAST tools integration (Checkmarx, SonarQube)
- More LLM models support
- YARA rule integration
- Binary instrumentation for deeper behavioral analysis


## 👤 Author

Chaimaekit
---

**Status**: v1.0 | **Last Updated**: March 2024
