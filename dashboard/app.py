import sys, os, json, io, hashlib, secrets, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import (Flask, render_template, send_file, request,
                   Response, stream_with_context, session, redirect, url_for, jsonify)
from core.report import load_all_reports
import config as cfg

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('VS_SECRET', 'vulnsentinel-change-me-in-production')

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
USERS_FILE    = os.path.join(BASE_DIR, 'vs_users.json')
SETTINGS_FILE = os.path.join(BASE_DIR, 'vs_settings.json')

DEFAULT_SETTINGS = {
    "llm_model":       "mistral:7b",
    "ollama_url":      "http://localhost:11434",
    "risk_threshold":  6,
    "sandbox_timeout": 30,
    "sandbox_memory":  "512m",
    "dashboard_port":  5000,
    "inference":       "CPU — no GPU required",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return {}

def save_users(u):
    with open(USERS_FILE, 'w') as f:
        json.dump(u, f, indent=2)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            s = json.load(f)
        for k, v in DEFAULT_SETTINGS.items():
            s.setdefault(k, v)
        return s
    return dict(DEFAULT_SETTINGS)

def save_settings(s):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(s, f, indent=2)

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def logged_in():
    return session.get('admin') is True

def admin_exists():
    return bool(load_users())

# ── routes ────────────────────────────────────────────────────────────────────

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if admin_exists():
        return redirect(url_for('login'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')
        if not username or not password:
            error = 'Username and password are required.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters.'
        elif password != confirm:
            error = 'Passwords do not match.'
        else:
            save_users({username: hash_pw(password)})
            session['admin']    = True
            session['username'] = username
            return redirect(url_for('dashboard'))
    return render_template('signup.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not admin_exists():
        return redirect(url_for('signup'))
    if logged_in():
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        users = load_users()
        if username in users and users[username] == hash_pw(password):
            session['admin']    = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
def dashboard():
    if not admin_exists():
        return redirect(url_for('signup'))
    if not logged_in():
        return redirect(url_for('login'))
    return render_template(
        'dashboard.html',
        reports=load_all_reports(),
        settings=load_settings(),
        username=session.get('username', 'admin')
    )

@app.route('/api/status')
def api_status():
    if not logged_in():
        return jsonify({'error': 'unauthorized'}), 401
    settings = load_settings()
    base_url = settings.get('ollama_url', 'http://localhost:11434')
    model    = settings.get('llm_model', 'mistral:7b')

    ollama_ok    = False
    model_loaded = False
    models_list  = []
    try:
        req = urllib.request.Request(
            f'{base_url}/api/tags',
            headers={'Content-Type': 'application/json'},
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            models_list  = [m.get('name', '') for m in data.get('models', [])]
            ollama_ok    = True
            model_loaded = any(model in m for m in models_list)
    except Exception:
        pass

    import shutil
    semgrep_available = shutil.which('semgrep') is not None
    docker_available  = shutil.which('docker') is not None

    return jsonify({
        'ollama_online':  ollama_ok,
        'model_loaded':   model_loaded,
        'model_name':     model,
        'models_list':    models_list,
        'ollama_url':     base_url,
        'semgrep':        semgrep_available,
        'docker':         docker_available,
        'risk_threshold': settings.get('risk_threshold', 6),
        'sandbox_memory': settings.get('sandbox_memory', '512m'),
    })


@app.route('/api/settings', methods=['POST'])
def api_settings():
    if not logged_in():
        return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json() or {}
    s = load_settings()
    int_fields = {'risk_threshold', 'sandbox_timeout', 'dashboard_port'}
    for k in DEFAULT_SETTINGS:
        if k in data:
            val = data[k]
            if k in int_fields:
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    pass
            s[k] = val
    save_settings(s)
    return jsonify({'ok': True, 'settings': s})


@app.route('/download/<path:report_file>')
def download_report(report_file):
    if not logged_in():
        return redirect(url_for('login'))
    report_file = os.path.basename(report_file)
    path = os.path.join(cfg.REPORTS_DIR, report_file)
    if not os.path.exists(path):
        for f in os.listdir(cfg.REPORTS_DIR):
            if f == report_file:
                path = os.path.join(cfg.REPORTS_DIR, f)
                break
        else:
            return f'Report not found: {report_file}', 404
    with open(path) as f:
        data = json.load(f)
    return send_file(
        io.BytesIO(json.dumps(data, indent=4).encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name=report_file
    )


@app.route('/api/chat', methods=['POST'])
def chat():
    if not logged_in():
        return jsonify({'error': 'unauthorized'}), 401
    message  = request.get_json().get('message', '')
    settings = load_settings()
    model    = settings.get('llm_model', 'mistral:7b')
    base_url = settings.get('ollama_url', 'http://localhost:11434')
    system = (
        'You are VulnSentinel AI, a security analyst assistant running fully locally. '
        'Specialise in vulnerability analysis, CVEs, binary exploitation, and security research. '
        'Be concise, technical, and precise. Use backticks for code and technical terms.'
    )

    def stream():
        try:
            payload = json.dumps({
                'model': model,
                'prompt': f'[SYSTEM]: {system}\n\n[USER]: {message}',
                'stream': True
            }).encode()
            req = urllib.request.Request(
                f'{base_url}/api/generate', data=payload,
                headers={'Content-Type': 'application/json'}, method='POST'
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                for line in resp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        token = obj.get('response', '')
                        if token:
                            yield f"data: {json.dumps({'token': token})}\n\n"
                        if obj.get('done'):
                            break
                    except json.JSONDecodeError:
                        continue
        except urllib.error.URLError as e:
            yield f"data: {json.dumps({'token': f'Cannot reach Ollama at {base_url}. Make sure Ollama is running (ollama serve).'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'token': f'Error: {str(e)}'})}\n\n"

    return Response(
        stream_with_context(stream()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


def start_dashboard():
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    start_dashboard()