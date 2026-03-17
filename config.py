import os
from dotenv import load_dotenv

load_dotenv()  
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")



BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
INCOMING_DIR   = os.path.join(BASE_DIR, "incoming")
REPORTS_DIR    = os.path.join(BASE_DIR, "reports")
LOGS_DIR       = os.path.join(BASE_DIR, "logs")
GHIDRA_PATH    = os.path.expanduser(
    "~/tools/ghidra_11.1.2_PUBLIC/support/analyzeHeadless"
)
GHIDRA_PROJECT = "/tmp/ghidra_projects"
GHIDRA_SCRIPTS = os.path.join(BASE_DIR, "ghidra_scripts")


OLLAMA_URL   = "http://localhost:11434/api/generate"
MODELS = {
    "fast": "mistral:7b",
    "deep": "mistral:7b",
}


RISK_THRESHOLD  = 6 
SANDBOX_TIMEOUT = 30 


SLACK_WEBHOOK = f"{SLACK_WEBHOOK_URL}"


SANDBOX_IMAGE  = "vulnsentinel-sandbox"
SANDBOX_MEMORY = "512m"
SANDBOX_CPUS   = "0.5"


DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 5000
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")


for _dir in [INCOMING_DIR, REPORTS_DIR, LOGS_DIR, GHIDRA_PROJECT, PROCESSED_DIR]:
    os.makedirs(_dir, exist_ok=True)