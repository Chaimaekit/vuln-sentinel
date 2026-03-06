from flask import Flask, jsonify, render_template_string, send_file
from core.report import load_all_reports
import json
import io

app = Flask(__name__)


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>VulnSentinel</title>
    <meta http-equiv="refresh" content="30">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', monospace;
            background: #0d1117;
            color: #c9d1d9;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container { width: 100%; max-width: 900px; }
        h1 { color: #58a6ff; margin-bottom: 5px; text-align: center; }
        .subtitle { color: #8b949e; margin-bottom: 30px; font-size: 13px; text-align: center; }
        
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 20px;
            margin: 15px 0;
            width: 100%;
            position: relative;
        }
        .critical { border-left: 5px solid #f85149; }
        .high     { border-left: 5px solid #e3b341; }
        .medium   { border-left: 5px solid #d29922; }
        .low      { border-left: 5px solid #3fb950; }

        .badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .badge-critical { background:#f8514933; color:#f85149; }
        .badge-high     { background:#e3b34133; color:#e3b341; }
        .badge-medium   { background:#d2992233; color:#d29922; }
        .badge-low      { background:#3fb95033; color:#3fb950; }

        .score { font-size: 32px; font-weight: bold; color: #58a6ff; line-height: 1; }
        .filename { font-size: 18px; font-weight: bold; color: #f0f6fc; margin-bottom: 8px; }
        .verdict { color: #c9d1d9; font-size: 14px; margin: 10px 0; font-style: italic; }
        .summary { color: #8b949e; font-size: 13px; line-height: 1.5; background: #0d1117; padding: 10px; border-radius: 4px; }
        .timestamp { color: #484f58; font-size: 11px; margin-top: 15px; }

        .btn-download {
            background: #21262d;
            color: #c9d1d9;
            border: 1px solid #30363d;
            padding: 5px 12px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 12px;
            transition: 0.2s;
        }
        .btn-download:hover { background: #30363d; border-color: #8b949e; }

        .stats { display: flex; gap: 15px; margin-bottom: 30px; justify-content: center; flex-wrap: wrap; }
        .stat { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 15px; text-align: center; min-width: 140px; }
        .stat-num { font-size: 24px; font-weight: bold; color: #58a6ff; }
        .stat-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡 VulnSentinel</h1>
        <p class="subtitle">Local Analysis Engine • Auto-refreshing</p>

        <div class="stats">
            <div class="stat"><div class="stat-num">{{ reports|length }}</div><div class="stat-label">Analyzed</div></div>
            <div class="stat"><div class="stat-num" style="color:#f85149">{{ reports|selectattr('risk_level','eq','critical')|list|length }}</div><div class="stat-label">Critical</div></div>
            <div class="stat"><div class="stat-num" style="color:#e3b341">{{ reports|selectattr('risk_level','eq','high')|list|length }}</div><div class="stat-label">High</div></div>
        </div>

        {% for r in reports %}
        <div class="card {{ r.risk_level }}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start">
                <div style="max-width: 80%;">
                    <div class="filename">{{ r.filename }}</div>
                    <span class="badge badge-{{ r.risk_level }}">{{ r.risk_level }}</span>
                    <div class="verdict">"{{ r.verdict }}"</div>
                    <div class="summary">{{ r.llm_analysis.summary }}</div>
                    <div class="timestamp">Analyzed at: {{ r.timestamp }}</div>
                </div>
                <div style="text-align: right;">
                    <div class="score">{{ r.risk_score }}<span style="font-size:14px; color:#484f58">/10</span></div>
                    <div style="margin-top: 20px;">
                        <a href="/download/{{ loop.index0 }}" class="btn-download">Download JSON</a>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    reports = load_all_reports()
    return render_template_string(HTML, reports=reports)

@app.route("/download/<int:report_id>")
def download_report(report_id):
    reports = load_all_reports()
    if 0 <= report_id < len(reports):
        report = reports[report_id]
        return send_file(
            io.BytesIO(json.dumps(report, indent=4).encode()),
            mimetype='application/json',
            as_attachment=True,
            download_name=f"report_{report.get('filename', 'analysis')}.json"
        )
    return "Report not found", 404

def start_dashboard():
    app.run(host="127.0.0.1", port=5000, debug=False)