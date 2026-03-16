import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template_string, send_file, request, Response, stream_with_context
from core.report import load_all_reports
import json, io, urllib.request
import config 

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VulnSentinel</title>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg:        #131211;
            --bg-raised: #1a1917;
            --bg-card:   #201e1c;
            --bg-card2:  #272422;
            --bg-hover:  #302d2a;
            --border:    #302d2a;
            --border-lo: #252220;
            --white:     #ffffff;
            --white-90:  #f0eeec;
            --white-70:  #c8c4c0;
            --white-50:  #8a8480;
            --white-30:  #585450;
            --br-hi:     #c89060;
            --br-mid:    #9a6c3c;
            --br-lo:     #6b4820;
            --br-bg:     #3a2510;
            --sev-crit:  #e06050;
            --sev-high:  #d09040;
            --sev-med:   #c0a830;
            --sev-low:   #78a868;
            --t: 0.16s ease;
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        html, body {
            height: 100%;
            font-family: 'IBM Plex Sans', sans-serif;
            background: var(--bg);
            color: var(--white-70);
            font-size: 14px;
            -webkit-font-smoothing: antialiased;
        }

        body { display: flex; overflow: hidden; }

        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

        /* ── SIDEBAR ── */
        .sidebar {
            width: 224px; min-width: 224px;
            background: var(--bg);
            border-right: 1px solid var(--border-lo);
            display: flex; flex-direction: column;
        }

        .brand { padding: 26px 22px 20px; border-bottom: 1px solid var(--border-lo); }
        .brand-name {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px; font-weight: 500;
            letter-spacing: 3px; text-transform: uppercase;
            color: var(--white);
        }
        .brand-sub {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
            color: var(--br-mid); margin-top: 5px;
        }

        .status-row {
            display: flex; align-items: center; gap: 8px;
            padding: 10px 22px; border-bottom: 1px solid var(--border-lo);
        }
        .led {
            width: 5px; height: 5px; border-radius: 50%;
            background: var(--sev-low); box-shadow: 0 0 5px var(--sev-low);
            animation: pulse 3.5s ease-in-out infinite;
        }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
        .status-text {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
            color: var(--sev-low);
        }

        .nav { flex: 1; padding: 18px 12px; display: flex; flex-direction: column; gap: 1px; }
        .nav-group {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 8px; letter-spacing: 2.5px; text-transform: uppercase;
            color: var(--white-30); padding: 0 10px; margin: 14px 0 6px;
        }
        .nav-group:first-child { margin-top: 0; }
        .nav-item {
            display: flex; align-items: center; gap: 10px;
            padding: 9px 12px; border-radius: 5px; cursor: pointer;
            font-size: 13px; color: var(--white-50);
            transition: background var(--t), color var(--t); user-select: none;
        }
        .nav-item:hover  { background: var(--bg-hover); color: var(--white-90); }
        .nav-item.active { background: var(--bg-card2); color: var(--white); }
        .nav-item svg    { width: 13px; height: 13px; flex-shrink: 0; opacity: .5; }
        .nav-item:hover svg, .nav-item.active svg { opacity: 1; }

        .sidebar-bottom { padding: 14px; border-top: 1px solid var(--border-lo); }
        .clear-btn {
            width: 100%; background: transparent;
            border: 1px solid var(--border); color: var(--white-50);
            padding: 8px; border-radius: 5px;
            font-size: 10px; font-family: 'IBM Plex Mono', monospace;
            letter-spacing: 1.5px; text-transform: uppercase;
            cursor: pointer; transition: all var(--t);
        }
        .clear-btn:hover { border-color: var(--br-lo); color: var(--br-hi); }

        /* ── MAIN ── */
        .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

        .topbar {
            height: 50px; background: var(--bg);
            border-bottom: 1px solid var(--border-lo);
            display: flex; align-items: center;
            padding: 0 30px; gap: 8px; flex-shrink: 0;
        }
        .tb-root { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--white-30); }
        .tb-sep  { color: var(--border); margin: 0 2px; }
        .tb-page { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--white-50); }
        .tb-spacer { flex: 1; }
        .refresh-btn {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;
            background: var(--bg-card); border: 1px solid var(--border);
            color: var(--white-50); padding: 6px 14px; border-radius: 5px;
            cursor: pointer; transition: all var(--t);
        }
        .refresh-btn:hover { border-color: var(--br-lo); color: var(--white-90); }

        /* ── PAGES ── */
        .page { display: none; flex: 1; overflow-y: auto; padding: 32px 30px; }
        .page.active { display: block; }
        #page-chat { padding: 0; display: none; flex-direction: column; }
        #page-chat.active { display: flex; }

        /* STATS */
        .stats-row {
            display: grid; grid-template-columns: repeat(4, 1fr);
            gap: 10px; margin-bottom: 32px;
        }
        .stat {
            background: var(--bg-card); border: 1px solid var(--border-lo);
            border-radius: 7px; padding: 20px; transition: border-color var(--t);
        }
        .stat:hover { border-color: var(--border); }
        .stat-num {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 28px; font-weight: 500; line-height: 1; color: var(--white);
        }
        .stat-num.crit { color: var(--sev-crit); }
        .stat-num.high { color: var(--sev-high); }
        .stat-num.safe { color: var(--sev-low);  }
        .stat-lbl {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
            color: var(--white-50); margin-top: 7px;
        }

        /* SECTION HEADER */
        .sec-hd {
            display: flex; align-items: baseline; gap: 14px;
            padding-bottom: 12px; margin-bottom: 16px;
            border-bottom: 1px solid var(--border-lo);
        }
        .sec-title { font-size: 13px; font-weight: 600; color: var(--white); }
        .sec-sub   { font-size: 12px; color: var(--white-50); }

        /* CARDS */
        .cards { display: flex; flex-direction: column; gap: 8px; }
        .rcard {
            background: var(--bg-card); border: 1px solid var(--border-lo);
            border-radius: 7px; overflow: hidden;
            transition: border-color var(--t), box-shadow var(--t);
        }
        .rcard:hover { border-color: var(--border); box-shadow: 0 2px 16px #00000030; }
        .rcard-row { display: flex; align-items: stretch; }

        .accent { width: 3px; flex-shrink: 0; }
        .accent.critical { background: var(--sev-crit); }
        .accent.high     { background: var(--sev-high); }
        .accent.medium   { background: var(--sev-med);  }
        .accent.low      { background: var(--sev-low);  }
        .accent.unknown  { background: var(--white-30); }

        .rcard-body {
            flex: 1; padding: 16px 20px;
            display: flex; align-items: center; gap: 16px;
        }
        .rcard-info { flex: 1; min-width: 0; }
        .nameline { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
        .filename {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 13px; font-weight: 500; color: var(--white);
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .sev-badge {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 9px; font-weight: 500; letter-spacing: 1.5px;
            text-transform: uppercase; padding: 2px 8px; border-radius: 3px; flex-shrink: 0;
        }
        .sev-badge.critical { color: var(--sev-crit); background: #e0605015; border: 1px solid #e0605040; }
        .sev-badge.high     { color: var(--sev-high); background: #d0904015; border: 1px solid #d0904040; }
        .sev-badge.medium   { color: var(--sev-med);  background: #c0a83015; border: 1px solid #c0a83040; }
        .sev-badge.low      { color: var(--sev-low);  background: #78a86815; border: 1px solid #78a86840; }
        .sev-badge.unknown  { color: var(--white-30); background: #58545015; border: 1px solid #58545040; }

        .verdict {
            font-size: 13px; color: var(--white-70);
            font-style: italic; margin-bottom: 8px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .toggle-btn {
            background: none; border: none; padding: 0;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px; letter-spacing: 1px; text-transform: uppercase;
            color: var(--white-30); cursor: pointer; transition: color var(--t);
        }
        .toggle-btn:hover { color: var(--br-hi); }

        .rcard-right {
            display: flex; flex-direction: column;
            align-items: flex-end; justify-content: center;
            gap: 10px; flex-shrink: 0;
        }
        .score {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 24px; font-weight: 500; line-height: 1;
        }
        .score .den { font-size: 12px; color: var(--white-30); }
        .score.critical { color: var(--sev-crit); }
        .score.high     { color: var(--sev-high); }
        .score.medium   { color: var(--sev-med);  }
        .score.low      { color: var(--sev-low);  }
        .score.unknown  { color: var(--white-30); }

        .dl-btn {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px; letter-spacing: 1px; text-transform: uppercase;
            color: var(--white-50); text-decoration: none;
            border: 1px solid var(--border); padding: 4px 10px; border-radius: 4px;
            transition: all var(--t);
        }
        .dl-btn:hover { border-color: var(--br-lo); color: var(--br-hi); }

        .summary-panel {
            display: none;
            padding: 14px 20px 16px 23px;
            background: var(--bg-raised); border-top: 1px solid var(--border-lo);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px; line-height: 1.8; color: var(--white-70);
        }
        .rcard-foot {
            padding: 7px 20px 9px 23px;
            border-top: 1px solid var(--border-lo); background: var(--bg-raised);
        }
        .ts { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--white-30); }

        /* EMPTY */
        .empty { text-align: center; padding: 80px 20px; }
        .empty-title {
            font-family: 'IBM Plex Mono', monospace; font-size: 11px;
            letter-spacing: 2px; text-transform: uppercase;
            color: var(--white-30); margin-bottom: 8px;
        }
        .empty-sub { font-size: 12px; color: var(--white-30); }

        /* ── CHAT ── */
        .chat-hd {
            padding: 20px 30px 16px; border-bottom: 1px solid var(--border-lo);
            background: var(--bg); flex-shrink: 0;
        }
        .chat-hd-title { font-size: 13px; font-weight: 600; color: var(--white); }
        .chips { display: flex; gap: 6px; margin-top: 6px; }
        .chip {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 9px; letter-spacing: 1.5px; text-transform: uppercase;
            padding: 2px 8px; border-radius: 3px;
        }
        .chip-model { color: var(--br-hi);   background: var(--bg-card2); border: 1px solid var(--br-lo); }
        .chip-local { color: var(--sev-low); background: #78a86810;       border: 1px solid #78a86830; }

        .chat-msgs {
            flex: 1; overflow-y: auto; padding: 24px 30px;
            display: flex; flex-direction: column; gap: 20px;
        }
        .msg { display: flex; gap: 12px; max-width: 800px; }
        .msg.user { align-self: flex-end; flex-direction: row-reverse; }
        .av {
            width: 28px; height: 28px; border-radius: 5px;
            display: flex; align-items: center; justify-content: center;
            font-family: 'IBM Plex Mono', monospace; font-size: 9px; font-weight: 500; flex-shrink: 0;
        }
        .msg.assistant .av { background: var(--bg-card2); border: 1px solid var(--border); color: var(--br-hi); }
        .msg.user      .av { background: var(--br-bg);    border: 1px solid var(--br-lo);  color: var(--br-hi); }
        .msg-body { flex: 1; }
        .msg-role {
            font-family: 'IBM Plex Mono', monospace; font-size: 9px;
            letter-spacing: 2px; text-transform: uppercase;
            margin-bottom: 6px; color: var(--white-30);
        }
        .msg.user .msg-role { text-align: right; }
        .bubble {
            padding: 13px 16px; border-radius: 6px;
            font-size: 13px; line-height: 1.75; color: var(--white-90);
        }
        .msg.assistant .bubble { background: var(--bg-card); border: 1px solid var(--border-lo); }
        .msg.user      .bubble { background: var(--br-bg);   border: 1px solid var(--br-lo); }
        .bubble code {
            font-family: 'IBM Plex Mono', monospace; font-size: 11px;
            background: var(--bg-raised); color: var(--br-hi);
            padding: 1px 5px; border-radius: 3px;
        }

        .typing { display: flex; gap: 5px; align-items: center; padding: 4px 0; }
        .tdot {
            width: 5px; height: 5px; border-radius: 50%;
            background: var(--br-mid); animation: tb 1.4s ease-in-out infinite;
        }
        .tdot:nth-child(2) { animation-delay: .18s; }
        .tdot:nth-child(3) { animation-delay: .36s; }
        @keyframes tb {
            0%,60%,100% { transform:translateY(0); opacity:.2; }
            30%          { transform:translateY(-5px); opacity:1; }
        }

        .chat-input-wrap {
            padding: 14px 30px 20px; border-top: 1px solid var(--border-lo);
            background: var(--bg); flex-shrink: 0;
        }
        .input-shell {
            display: flex; align-items: flex-end; gap: 10px;
            background: var(--bg-card); border: 1px solid var(--border);
            border-radius: 7px; padding: 10px 14px; transition: border-color var(--t);
        }
        .input-shell:focus-within { border-color: var(--br-lo); }
        #chatInput {
            flex: 1; background: none; border: none; outline: none;
            resize: none; font-family: 'IBM Plex Sans', sans-serif;
            font-size: 13px; color: var(--white); line-height: 1.5;
            min-height: 22px; max-height: 120px;
        }
        #chatInput::placeholder { color: var(--white-30); }
        .send-btn {
            background: var(--br-bg); border: 1px solid var(--br-lo); color: var(--br-hi);
            width: 30px; height: 30px; border-radius: 5px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0; transition: all var(--t);
        }
        .send-btn:hover    { background: var(--br-lo); color: var(--white); }
        .send-btn:disabled { opacity: .3; cursor: not-allowed; }
        .input-hint {
            font-family: 'IBM Plex Mono', monospace; font-size: 9px;
            color: var(--white-30); text-align: center; margin-top: 7px;
            letter-spacing: .8px; text-transform: uppercase;
        }

        /* ── SETTINGS ── */
        .settings-list { display: flex; flex-direction: column; gap: 6px; margin-top: 4px; }
        .srow {
            background: var(--bg-card); border: 1px solid var(--border-lo);
            border-radius: 6px; padding: 13px 18px;
            display: flex; justify-content: space-between; align-items: center;
            transition: border-color var(--t);
        }
        .srow:hover { border-color: var(--border); }
        .skey { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--white-50); letter-spacing: .8px; }
        .sval { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--br-hi); }
    </style>
</head>
<body>

<aside class="sidebar">
    <div class="brand">
        <div class="brand-name">VulnSentinel</div>
        <div class="brand-sub">Cyber Defense Platform</div>
    </div>
    <div class="status-row">
        <div class="led"></div>
        <span class="status-text">Pipeline Online</span>
    </div>
    <nav class="nav">
        <div class="nav-group">Workspace</div>
        <div class="nav-item active" onclick="nav(this,'analysis','DETECTION_FEED')">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4">
                <rect x="1" y="1" width="6" height="6" rx="1.2"/>
                <rect x="9" y="1" width="6" height="6" rx="1.2"/>
                <rect x="1" y="9" width="6" height="6" rx="1.2"/>
                <rect x="9" y="9" width="6" height="6" rx="1.2"/>
            </svg>
            Analysis
        </div>
        <div class="nav-item" onclick="nav(this,'chat','AI_ASSISTANT')">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4">
                <path d="M13 9.5a1.5 1.5 0 01-1.5 1.5H5L2 14V3.5A1.5 1.5 0 013.5 2h8A1.5 1.5 0 0113 3.5z"/>
            </svg>
            AI Chat
        </div>
        <div class="nav-group">System</div>
        <div class="nav-item" onclick="nav(this,'settings','SETTINGS')">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4">
                <circle cx="8" cy="8" r="2.2"/>
                <path d="M8 1.5v1.8M8 12.7v1.8M1.5 8h1.8M12.7 8h1.8M3.4 3.4l1.3 1.3M11.3 11.3l1.3 1.3M3.4 12.6l1.3-1.3M11.3 4.7l1.3-1.3"/>
            </svg>
            Settings
        </div>
    </nav>
    <div class="sidebar-bottom">
        <button class="clear-btn" onclick="clearChat()">Clear Chat</button>
    </div>
</aside>

<div class="main">
    <div class="topbar">
        <span class="tb-root">vulnsentinel</span>
        <span class="tb-sep">/</span>
        <span class="tb-page" id="tbTitle">DETECTION_FEED</span>
        <div class="tb-spacer"></div>
        <button class="refresh-btn" onclick="location.reload()">Refresh</button>
    </div>

    <!-- ANALYSIS PAGE -->
    <div class="page active" id="page-analysis">
        <div class="stats-row">
            <div class="stat">
                <div class="stat-num">{{ reports|length }}</div>
                <div class="stat-lbl">Total Scans</div>
            </div>
            <div class="stat">
                <div class="stat-num crit">{{ reports|selectattr('risk_level','eq','critical')|list|length }}</div>
                <div class="stat-lbl">Critical</div>
            </div>
            <div class="stat">
                <div class="stat-num high">{{ reports|selectattr('risk_level','eq','high')|list|length }}</div>
                <div class="stat-lbl">High</div>
            </div>
            <div class="stat">
                <div class="stat-num safe">{{ reports|selectattr('risk_level','eq','low')|list|length }}</div>
                <div class="stat-lbl">Safe</div>
            </div>
        </div>

        <div class="sec-hd">
            <span class="sec-title">Detection Feed</span>
            <span class="sec-sub">All analyzed files — sorted by risk</span>
        </div>

        <div class="cards">
        {% if reports %}
            {% for r in reports %}
            {% set lvl = r.risk_level if r.risk_level in ['critical','high','medium','low'] else 'unknown' %}
            {% set score = r.risk_score if r.risk_score is defined else 0 %}
            {% set verdict = r.verdict if r.verdict is defined else (r.llm_analysis.verdict if r.llm_analysis is defined else 'No verdict') %}
            {% set summary = r.llm_analysis.summary if r.llm_analysis is defined else 'No summary available.' %}
            <div class="rcard">
                <div class="rcard-row">
                    <div class="accent {{ lvl }}"></div>
                    <div class="rcard-body">
                        <div class="rcard-info">
                            <div class="nameline">
                                <span class="filename">{{ r.filename }}</span>
                                <span class="sev-badge {{ lvl }}">{{ lvl }}</span>
                            </div>
                            <div class="verdict">{{ verdict }}</div>
                            <button class="toggle-btn" onclick="toggleSummary(this)">+ view summary</button>
                        </div>
                        <div class="rcard-right">
                            <div class="score {{ lvl }}">{{ score }}<span class="den">/10</span></div>
                            <a href="/download/{{ r.report_file }}" class="dl-btn">export json</a>
                        </div>
                    </div>
                </div>
                <div class="summary-panel">
                    <div style="margin-bottom:10px">{{ summary }}</div>
                    {% if r.signal_scores is defined %}
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px">
                        <div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:4px;padding:8px 10px">
                            <div style="font-size:9px;letter-spacing:2px;color:var(--white-30);margin-bottom:4px">RULES ENGINE</div>
                            <div style="font-size:18px;font-weight:500;color:var(--br-hi);font-family:'IBM Plex Mono',monospace">{{ r.signal_scores.rules_score }}<span style="font-size:10px;color:var(--white-30)">/10</span></div>
                            <div style="font-size:9px;color:var(--white-30);margin-top:4px;font-family:'IBM Plex Mono',monospace">DETERMINISTIC</div>
                        </div>
                        <div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:4px;padding:8px 10px">
                            <div style="font-size:9px;letter-spacing:2px;color:var(--white-30);margin-bottom:4px">LLM SCORE</div>
                            <div style="font-size:18px;font-weight:500;color:var(--br-hi);font-family:'IBM Plex Mono',monospace">{{ r.signal_scores.llm_score }}<span style="font-size:10px;color:var(--white-30)">/10</span></div>
                            <div style="font-size:9px;color:var(--white-30);margin-top:4px;font-family:'IBM Plex Mono',monospace">CONF: {{ r.signal_scores.llm_confidence }}/10</div>
                        </div>
                        <div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:4px;padding:8px 10px">
                            <div style="font-size:9px;letter-spacing:2px;color:var(--white-30);margin-bottom:4px">SEMGREP</div>
                            <div style="font-size:18px;font-weight:500;color:var(--br-hi);font-family:'IBM Plex Mono',monospace">{{ r.signal_scores.semgrep_count }}<span style="font-size:10px;color:var(--white-30)"> findings</span></div>
                            <div style="font-size:9px;color:var(--white-30);margin-top:4px;font-family:'IBM Plex Mono',monospace">PATTERN MATCH</div>
                        </div>
                        <div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:4px;padding:8px 10px">
                            <div style="font-size:9px;letter-spacing:2px;color:var(--white-30);margin-bottom:4px">SANDBOX</div>
                            <div style="font-size:18px;font-weight:500;font-family:'IBM Plex Mono',monospace;
                                {% if r.signal_scores.sandbox_threat %}color:var(--sev-crit){% else %}color:var(--sev-low){% endif %}">
                                {% if not r.signal_scores.sandbox_ran %}—
                                {% elif r.signal_scores.sandbox_threat %}THREAT
                                {% else %}CLEAN{% endif %}
                            </div>
                            <div style="font-size:9px;color:var(--white-30);margin-top:4px;font-family:'IBM Plex Mono',monospace">GROUND TRUTH</div>
                        </div>
                    </div>
                    {% if r.decision is defined and r.decision.signals is defined %}
                    <div style="margin-top:10px;padding:8px 10px;background:var(--bg-card2);border:1px solid var(--border);border-radius:4px">
                        <div style="font-size:9px;letter-spacing:2px;color:var(--white-30);margin-bottom:6px">VOTE BREAKDOWN</div>
                        {% for sig in r.decision.signals %}
                        <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--white-50);margin-bottom:2px">· {{ sig }}</div>
                        {% endfor %}
                        <div style="margin-top:6px;font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--br-hi)">
                            → {{ r.decision.final_action }} ({{ r.decision.confidence }} confidence)
                        </div>
                    </div>
                    {% endif %}
                    {% endif %}
                </div>
                <div class="rcard-foot"><span class="ts">{{ r.timestamp }}</span></div>
            </div>
            {% endfor %}
        {% else %}
            <div class="empty">
                <div class="empty-title">No reports yet</div>
                <div class="empty-sub">Drop a file into incoming/ to begin analysis</div>
            </div>
        {% endif %}
        </div>
    </div>

    <!-- CHAT PAGE -->
    <div class="page" id="page-chat">
        <div class="chat-hd">
            <div class="chat-hd-title">AI Security Assistant</div>
            <div class="chips">
                <span class="chip chip-model">mistral:7b</span>
                <span class="chip chip-local">fully local</span>
            </div>
        </div>
        <div class="chat-msgs" id="chatMsgs">
            <div class="msg assistant">
                <div class="av">VS</div>
                <div class="msg-body">
                    <div class="msg-role">Assistant</div>
                    <div class="bubble">
                        VulnSentinel AI is ready. Ask me about scan results, CVEs,
                        vulnerability classes, or static and dynamic analysis techniques.<br><br>
                        All inference runs locally — nothing leaves your VM.
                    </div>
                </div>
            </div>
        </div>
        <div class="chat-input-wrap">
            <div class="input-shell">
                <textarea id="chatInput" rows="1"
                    placeholder="Ask about a vulnerability, CVE, or scan result..."
                    onkeydown="onKey(event)"
                    oninput="grow(this)"></textarea>
                <button class="send-btn" id="sendBtn" onclick="send()">
                    <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M1.5 1.5l13 6.5-13 6.5V9.5l9-2.5-9-2.5V1.5z"/>
                    </svg>
                </button>
            </div>
            <div class="input-hint">Enter · send &nbsp;·&nbsp; Shift+Enter · new line</div>
        </div>
    </div>

    <!-- SETTINGS PAGE -->
    <div class="page" id="page-settings">
        <div class="sec-hd">
            <span class="sec-title">Configuration</span>
            <span class="sec-sub">Current pipeline settings</span>
        </div>
        <div class="settings-list">
            <div class="srow"><span class="skey">LLM_MODEL</span><span class="sval">mistral:7b</span></div>
            <div class="srow"><span class="skey">OLLAMA_URL</span><span class="sval">http://localhost:11434</span></div>
            <div class="srow"><span class="skey">RISK_THRESHOLD</span><span class="sval">6 / 10</span></div>
            <div class="srow"><span class="skey">SANDBOX_TIMEOUT</span><span class="sval">30s</span></div>
            <div class="srow"><span class="skey">SANDBOX_MEMORY</span><span class="sval">512m</span></div>
            <div class="srow"><span class="skey">DASHBOARD_PORT</span><span class="sval">5000</span></div>
            <div class="srow"><span class="skey">INFERENCE</span><span class="sval">CPU — no GPU required</span></div>
        </div>
    </div>
</div>

<script>
function nav(el, id, title) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('page-' + id).classList.add('active');
    el.classList.add('active');
    document.getElementById('tbTitle').textContent = title;
}

function toggleSummary(btn) {
    const p = btn.closest('.rcard').querySelector('.summary-panel');
    const open = p.style.display === 'block';
    p.style.display = open ? 'none' : 'block';
    btn.textContent = open ? '+ view summary' : '- hide summary';
}

const msgsEl = document.getElementById('chatMsgs');
function grow(el) { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 120) + 'px'; }
function onKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }
function bottom() { msgsEl.scrollTop = msgsEl.scrollHeight; }

function addMsg(role, html) {
    const d = document.createElement('div');
    d.className = 'msg ' + role;
    d.innerHTML = `
        <div class="av">${role === 'assistant' ? 'VS' : 'AN'}</div>
        <div class="msg-body">
            <div class="msg-role">${role === 'assistant' ? 'Assistant' : 'You'}</div>
            <div class="bubble">${html}</div>
        </div>`;
    msgsEl.appendChild(d);
    bottom();
    return d.querySelector('.bubble');
}

function showTyping() {
    const d = document.createElement('div');
    d.className = 'msg assistant'; d.id = 'typing';
    d.innerHTML = `
        <div class="av">VS</div>
        <div class="msg-body">
            <div class="msg-role">Assistant</div>
            <div class="bubble"><div class="typing">
                <div class="tdot"></div><div class="tdot"></div><div class="tdot"></div>
            </div></div>
        </div>`;
    msgsEl.appendChild(d); bottom();
}

function removeTyping() { const t = document.getElementById('typing'); if (t) t.remove(); }

async function send() {
    const inp = document.getElementById('chatInput');
    const btn = document.getElementById('sendBtn');
    const txt = inp.value.trim();
    if (!txt) return;
    inp.value = ''; inp.style.height = 'auto'; btn.disabled = true;
    addMsg('user', esc(txt));
    showTyping();
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: txt })
        });
        removeTyping();
        const bub = addMsg('assistant', '');
        const rdr = res.body.getReader();
        const dec = new TextDecoder();
        let full = '';
        while (true) {
            const { done, value } = await rdr.read();
            if (done) break;
            dec.decode(value).split('\\n').filter(l => l.startsWith('data:')).forEach(l => {
                try {
                    const d = JSON.parse(l.slice(5));
                    if (d.token) { full += d.token; bub.innerHTML = fmt(full); bottom(); }
                } catch {}
            });
        }
    } catch {
        removeTyping();
        addMsg('assistant', 'Could not reach Ollama. Verify it is running on port 11434.');
    }
    btn.disabled = false; inp.focus();
}

function fmt(t) { return esc(t).replace(/`([^`\\n]+)`/g,'<code>$1</code>').replace(/\\n/g,'<br>'); }
function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function clearChat() {
    msgsEl.innerHTML = `
        <div class="msg assistant">
            <div class="av">VS</div>
            <div class="msg-body">
                <div class="msg-role">Assistant</div>
                <div class="bubble">Chat cleared. Ready when you are.</div>
            </div>
        </div>`;
}
</script>
</body>
</html>
"""


@app.route("/")
def dashboard():
    reports = load_all_reports()
    return render_template_string(HTML, reports=reports)


@app.route("/download/<path:report_file>")
def download_report(report_file):
    report_file = os.path.basename(report_file)
    path = os.path.join(config.REPORTS_DIR, report_file)

    if not os.path.exists(path):
        for f in os.listdir(config.REPORTS_DIR):
            if f == report_file:
                path = os.path.join(config.REPORTS_DIR, f)
                break
        else:
            return f"Report not found: {report_file}", 404

    with open(path) as f:
        data = json.load(f)

    return send_file(
        io.BytesIO(json.dumps(data, indent=4).encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name=report_file
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    message = request.get_json().get("message", "")
    system = (
        "You are VulnSentinel AI, a security analyst assistant running fully locally. "
        "Specialise in vulnerability analysis, CVEs, binary exploitation, and security research. "
        "Be concise, technical, and precise. Use backticks for code and technical terms."
    )

    def stream():
        try:
            payload = json.dumps({
                "model": "mistral:7b",
                "prompt": f"[SYSTEM]: {system}\n\n[USER]: {message}",
                "stream": True
            }).encode()
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                for line in resp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        token = obj.get("response", "")
                        if token:
                            yield f"data: {json.dumps({'token': token})}\n\n"
                        if obj.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            yield f"data: {json.dumps({'token': f'Error: {e}'})}\n\n"

    return Response(
        stream_with_context(stream()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


def start_dashboard():
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    start_dashboard()