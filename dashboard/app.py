import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template_string, send_file, request, Response, stream_with_context
from core.report import load_all_reports
import json, io, urllib.request
import config

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VulnSentinel</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="icon" type="image/svg+xml" id="favicon-link">
    <style>
        :root, [data-theme="light"] {
            --bg:        #ffffff;
            --bg-off:    #f7f7f5;
            --bg-card:   #f2f2f0;
            --border:    #e0e0dc;
            --black:     #0a0a0a;
            --gray-hi:   #3a3a3a;
            --gray-mid:  #6b6b6b;
            --gray-lo:   #9a9a9a;
            --gray-xlo:  #c8c8c4;
            --red:       #c42b2b;
            --orange:    #bf6010;
            --yellow:    #9a7e00;
            --green:     #1f7035;
            --shield:    #0a0a0a;
            --t: 0.18s ease;
        }

        [data-theme="dark"] {
            --bg:        #111111;
            --bg-off:    #1a1a1a;
            --bg-card:   #222222;
            --border:    #2e2e2e;
            --black:     #f0f0ee;
            --gray-hi:   #c8c8c4;
            --gray-mid:  #888884;
            --gray-lo:   #555552;
            --gray-xlo:  #333330;
            --red:       #e05050;
            --orange:    #e07830;
            --yellow:    #c8a820;
            --green:     #3aaa60;
            --shield:    #f0f0ee;
            --t: 0.18s ease;
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        html, body {
            height: 100%;
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--black);
            font-size: 14px;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
            transition: background 0.2s ease, color 0.2s ease;
        }

        body { display: flex; overflow: hidden; }

        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

        .sidebar {
            width: 220px; min-width: 220px;
            background: var(--bg);
            border-right: 1px solid var(--border);
            display: flex; flex-direction: column;
            transition: background 0.2s ease, border-color 0.2s ease;
        }

        .brand { padding: 28px 24px 24px; border-bottom: 1px solid var(--border); }
        .brand-logo { display: flex; align-items: center; gap: 10px; }
        .brand-logo svg { width: 34px; height: 34px; flex-shrink: 0; }
        .brand-name {
            font-family: 'DM Sans', sans-serif;
            font-size: 15px; font-weight: 700;
            letter-spacing: -0.2px; color: var(--black); line-height: 1;
        }

        .nav { flex: 1; padding: 16px 12px; display: flex; flex-direction: column; gap: 1px; }
        .nav-item {
            display: flex; align-items: center;
            padding: 9px 12px; border-radius: 6px; cursor: pointer;
            font-family: 'DM Sans', sans-serif;
            font-size: 14px; font-weight: 500;
            color: var(--gray-mid);
            transition: background var(--t), color var(--t); user-select: none;
            justify-content: space-between;
        }
        .nav-item:hover  { background: var(--bg-card); color: var(--black); }
        .nav-item.active { color: var(--black); background: var(--bg-card); }
        .nav-chevron { font-size: 13px; opacity: 0.35; }
        .nav-item-inner { display: flex; align-items: center; gap: 10px; }
        .nav-item svg { width: 14px; height: 14px; flex-shrink: 0; stroke: currentColor; fill: none; opacity: 0.5; }
        .nav-item:hover svg, .nav-item.active svg { opacity: 0.9; }
        .nav-sep { height: 1px; background: var(--border); margin: 10px 0; }

        .sidebar-bottom {
            padding: 16px 12px; border-top: 1px solid var(--border);
            display: flex; flex-direction: column; gap: 8px;
        }
        .sb-btn {
            width: 100%; background: var(--black); border: none; color: var(--bg);
            padding: 10px 14px; border-radius: 8px;
            font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500;
            cursor: pointer; transition: opacity var(--t); text-align: center;
        }
        .sb-btn:hover { opacity: 0.78; }
        .sb-btn.secondary {
            background: transparent; border: 1px solid var(--border); color: var(--gray-mid);
        }
        .sb-btn.secondary:hover { background: var(--bg-card); color: var(--black); }

        .theme-toggle {
            display: flex; align-items: center; justify-content: space-between;
            padding: 8px 12px; border-radius: 6px; cursor: pointer;
            font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500;
            color: var(--gray-mid); transition: background var(--t), color var(--t);
        }
        .theme-toggle:hover { background: var(--bg-card); color: var(--black); }
        .toggle-track {
            width: 32px; height: 18px; border-radius: 100px;
            background: var(--border); position: relative;
            transition: background 0.2s ease; flex-shrink: 0;
        }
        .toggle-track.on { background: var(--black); }
        .toggle-thumb {
            position: absolute; top: 3px; left: 3px;
            width: 12px; height: 12px; border-radius: 50%;
            background: var(--bg); transition: transform 0.2s ease, background 0.2s ease;
        }
        .toggle-track.on .toggle-thumb { transform: translateX(14px); }

        .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

        .topbar {
            height: 52px; background: var(--bg); border-bottom: 1px solid var(--border);
            display: flex; align-items: center; padding: 0 36px; gap: 8px; flex-shrink: 0;
            transition: background 0.2s ease, border-color 0.2s ease;
        }
        .tb-logo { font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 700; color: var(--black); letter-spacing: -0.2px; }
        .tb-sep  { color: var(--gray-xlo); margin: 0 6px; font-size: 15px; }
        .tb-page { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 400; color: var(--gray-mid); }
        .tb-spacer { flex: 1; }
        .status-pill {
            display: flex; align-items: center; gap: 6px;
            background: var(--bg-card); border: 1px solid var(--border);
            padding: 5px 12px; border-radius: 100px;
            font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500; color: var(--gray-mid);
        }
        .led { width: 6px; height: 6px; border-radius: 50%; background: var(--green); animation: pulse 3s ease-in-out infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

        .page { display: none; flex: 1; overflow-y: auto; padding: 44px 36px; }
        .page.active { display: block; }
        #page-chat { padding: 0; display: none; flex-direction: column; }
        #page-chat.active { display: flex; }

        .hero { margin-bottom: 44px; }
        .hero-label {
            font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600;
            letter-spacing: 1.8px; text-transform: uppercase; color: var(--gray-lo); margin-bottom: 14px;
        }
        .hero-title {
            font-family: 'DM Sans', sans-serif; font-size: 42px; font-weight: 700;
            line-height: 1.1; letter-spacing: -1px; color: var(--black);
        }

        .stats-row {
            display: grid; grid-template-columns: repeat(4, 1fr);
            gap: 1px; margin-bottom: 48px;
            background: var(--border); border: 1px solid var(--border);
            border-radius: 10px; overflow: hidden;
        }
        .stat { background: var(--bg); padding: 24px 22px; transition: background var(--t); }
        .stat:hover { background: var(--bg-off); }
        .stat-label {
            font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 600;
            letter-spacing: 1.8px; text-transform: uppercase; color: var(--gray-lo); margin-bottom: 10px;
        }
        .stat-num {
            font-family: 'DM Sans', sans-serif; font-size: 36px; font-weight: 700;
            line-height: 1; letter-spacing: -0.5px; color: var(--black);
        }
        .stat-num.crit { color: var(--red); }
        .stat-num.high { color: var(--orange); }
        .stat-num.safe { color: var(--green); }

        .sec-hd { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
        .sec-label {
            font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 600;
            letter-spacing: 1.8px; text-transform: uppercase; color: var(--gray-lo);
        }
        .sec-count { font-family: 'Inter', sans-serif; font-size: 12px; color: var(--gray-lo); }

        .cards { display: flex; flex-direction: column; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
        .rcard { background: var(--bg); border-bottom: 1px solid var(--border); transition: background var(--t); }
        .rcard:last-child { border-bottom: none; }
        .rcard:hover { background: var(--bg-off); }
        .rcard-row { display: flex; align-items: stretch; }

        .accent { width: 3px; flex-shrink: 0; }
        .accent.critical { background: var(--red); }
        .accent.high     { background: var(--orange); }
        .accent.medium   { background: var(--yellow); }
        .accent.low      { background: var(--green); }
        .accent.unknown  { background: var(--gray-xlo); }

        .rcard-body { flex: 1; padding: 18px 22px; display: flex; align-items: center; gap: 20px; }
        .rcard-info { flex: 1; min-width: 0; }
        .nameline { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
        .filename {
            font-family: 'DM Sans', sans-serif; font-size: 15px; font-weight: 600;
            color: var(--black); letter-spacing: -0.2px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .sev-badge {
            font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 600;
            letter-spacing: 1px; text-transform: uppercase;
            padding: 2px 8px; border-radius: 100px; flex-shrink: 0;
        }
        .sev-badge.critical { color: var(--red);    background: rgba(196,43,43,0.08);  border: 1px solid rgba(196,43,43,0.2); }
        .sev-badge.high     { color: var(--orange);  background: rgba(191,96,16,0.08);  border: 1px solid rgba(191,96,16,0.2); }
        .sev-badge.medium   { color: var(--yellow);  background: rgba(154,126,0,0.08);  border: 1px solid rgba(154,126,0,0.2); }
        .sev-badge.low      { color: var(--green);   background: rgba(31,112,53,0.08);  border: 1px solid rgba(31,112,53,0.2); }
        .sev-badge.unknown  { color: var(--gray-lo); background: rgba(154,154,154,0.08);border: 1px solid rgba(154,154,154,0.2); }

        .verdict { font-family: 'Inter', sans-serif; font-size: 13px; color: var(--gray-mid); margin-bottom: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .toggle-btn {
            background: none; border: 1px solid var(--border); padding: 4px 12px; border-radius: 100px;
            font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 500;
            color: var(--gray-mid); cursor: pointer; transition: all var(--t);
        }
        .toggle-btn:hover { background: var(--bg-card); color: var(--black); border-color: var(--gray-xlo); }

        .rcard-right { display: flex; flex-direction: column; align-items: flex-end; justify-content: center; gap: 10px; flex-shrink: 0; }
        .score { font-family: 'DM Sans', sans-serif; font-size: 26px; font-weight: 700; line-height: 1; letter-spacing: -0.5px; }
        .score .den { font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 400; color: var(--gray-lo); }
        .score.critical { color: var(--red); }
        .score.high     { color: var(--orange); }
        .score.medium   { color: var(--yellow); }
        .score.low      { color: var(--green); }
        .score.unknown  { color: var(--gray-lo); }

        .dl-btn {
            font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 500;
            color: var(--gray-mid); text-decoration: none;
            border: 1px solid var(--border); padding: 5px 12px; border-radius: 100px; transition: all var(--t);
        }
        .dl-btn:hover { border-color: var(--black); color: var(--black); }

        .summary-panel {
            display: none; padding: 16px 22px 20px 25px;
            background: var(--bg-off); border-top: 1px solid var(--border);
            font-family: 'Inter', sans-serif; font-size: 13px; line-height: 1.8; color: var(--gray-hi);
        }
        .rcard-foot {
            padding: 8px 22px 10px 25px; border-top: 1px solid var(--border); background: var(--bg-off);
        }
        .ts { font-family: 'Inter', sans-serif; font-size: 11px; color: var(--gray-lo); }

        .signal-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 16px; }
        .signal-box { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; }
        .signal-label {
            font-family: 'Inter', sans-serif; font-size: 9px; font-weight: 600;
            letter-spacing: 1.8px; text-transform: uppercase; color: var(--gray-lo); margin-bottom: 8px;
        }
        .signal-val { font-family: 'DM Sans', sans-serif; font-size: 20px; font-weight: 700; line-height: 1; letter-spacing: -0.3px; color: var(--black); }
        .signal-val .den { font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 400; color: var(--gray-lo); }
        .signal-sub { font-family: 'Inter', sans-serif; font-size: 10px; color: var(--gray-lo); margin-top: 4px; }

        .empty { padding: 60px 24px; }
        .empty-title { font-family: 'DM Sans', sans-serif; font-size: 20px; font-weight: 700; letter-spacing: -0.3px; color: var(--black); margin-bottom: 6px; }
        .empty-sub { font-family: 'Inter', sans-serif; font-size: 13px; color: var(--gray-lo); }

        .chat-hd { padding: 24px 36px 18px; border-bottom: 1px solid var(--border); background: var(--bg); flex-shrink: 0; }
        .chat-hd-title { font-family: 'DM Sans', sans-serif; font-size: 22px; font-weight: 700; letter-spacing: -0.4px; color: var(--black); margin-bottom: 8px; }
        .chips { display: flex; gap: 6px; }
        .chip { font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; padding: 3px 10px; border-radius: 100px; }
        .chip-model { color: var(--gray-hi); background: var(--bg-card); border: 1px solid var(--border); }
        .chip-local { color: var(--green); background: rgba(31,112,53,0.08); border: 1px solid rgba(31,112,53,0.2); }

        .chat-msgs { flex: 1; overflow-y: auto; padding: 28px 36px; display: flex; flex-direction: column; gap: 22px; }
        .msg { display: flex; gap: 12px; max-width: 720px; }
        .msg.user { align-self: flex-end; flex-direction: row-reverse; }
        .av { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-family: 'DM Sans', sans-serif; font-size: 10px; font-weight: 700; flex-shrink: 0; }
        .msg.assistant .av { background: var(--black); color: var(--bg); }
        .msg.user      .av { background: var(--bg-card); border: 1px solid var(--border); color: var(--gray-mid); }
        .msg-body { flex: 1; }
        .msg-role { font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 600; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 6px; color: var(--gray-lo); }
        .msg.user .msg-role { text-align: right; }
        .bubble { padding: 13px 16px; border-radius: 10px; font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.75; color: var(--gray-hi); }
        .msg.assistant .bubble { background: var(--bg-off); border: 1px solid var(--border); }
        .msg.user      .bubble { background: var(--black); color: var(--bg); }
        .bubble code { font-family: 'Courier New', monospace; font-size: 12px; background: var(--bg-card); color: var(--black); padding: 1px 5px; border-radius: 3px; }

        .typing { display: flex; gap: 5px; align-items: center; padding: 4px 0; }
        .tdot { width: 5px; height: 5px; border-radius: 50%; background: var(--gray-xlo); animation: tb 1.4s ease-in-out infinite; }
        .tdot:nth-child(2) { animation-delay: .18s; }
        .tdot:nth-child(3) { animation-delay: .36s; }
        @keyframes tb { 0%,60%,100%{transform:translateY(0);opacity:.3} 30%{transform:translateY(-5px);opacity:1} }

        .chat-input-wrap { padding: 14px 36px 22px; border-top: 1px solid var(--border); background: var(--bg); flex-shrink: 0; }
        .input-shell { display: flex; align-items: flex-end; gap: 10px; background: var(--bg-off); border: 1px solid var(--border); border-radius: 10px; padding: 11px 14px; transition: border-color var(--t); }
        .input-shell:focus-within { border-color: var(--black); }
        #chatInput { flex: 1; background: none; border: none; outline: none; resize: none; font-family: 'Inter', sans-serif; font-size: 14px; color: var(--black); line-height: 1.5; min-height: 22px; max-height: 120px; }
        #chatInput::placeholder { color: var(--gray-lo); }
        .send-btn { background: var(--black); border: none; color: var(--bg); width: 30px; height: 30px; border-radius: 7px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: opacity var(--t); }
        .send-btn:hover    { opacity: 0.75; }
        .send-btn:disabled { opacity: .25; cursor: not-allowed; }
        .input-hint { font-family: 'Inter', sans-serif; font-size: 11px; color: var(--gray-lo); text-align: center; margin-top: 8px; }

        .settings-list { display: flex; flex-direction: column; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
        .srow { background: var(--bg); border-bottom: 1px solid var(--border); padding: 14px 22px; display: flex; justify-content: space-between; align-items: center; transition: background var(--t); }
        .srow:last-child { border-bottom: none; }
        .srow:hover { background: var(--bg-off); }
        .skey { font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500; color: var(--black); }
        .sval { font-family: 'Inter', sans-serif; font-size: 13px; color: var(--gray-mid); }
    </style>
</head>
<body>

<aside class="sidebar">
    <div class="brand">
        <div class="brand-logo">
            <svg viewBox="0 0 34 34" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M17 2L3 8.5v9.5c0 7.5 5.8 13.8 14 15.5C25.2 31.8 31 25.5 31 18V8.5L17 2z" fill="var(--shield)"/>
            </svg>
            <div class="brand-name">VulnSentinel</div>
        </div>
    </div>
    <nav class="nav">
        <div class="nav-item active" onclick="nav(this,'analysis','Detection Feed')">
            <div class="nav-item-inner">
                <svg viewBox="0 0 16 16" stroke-width="1.5">
                    <rect x="1" y="1" width="6" height="6" rx="1"/>
                    <rect x="9" y="1" width="6" height="6" rx="1"/>
                    <rect x="1" y="9" width="6" height="6" rx="1"/>
                    <rect x="9" y="9" width="6" height="6" rx="1"/>
                </svg>
                Analysis
            </div>
        </div>
        <div class="nav-item" onclick="nav(this,'chat','AI Assistant')">
            <div class="nav-item-inner">
                <svg viewBox="0 0 16 16" stroke-width="1.5">
                    <path d="M13 9.5a1.5 1.5 0 01-1.5 1.5H5L2 14V3.5A1.5 1.5 0 013.5 2h8A1.5 1.5 0 0113 3.5z"/>
                </svg>
                AI Chat
            </div>
            <span class="nav-chevron">›</span>
        </div>
        <div class="nav-sep"></div>
        <div class="nav-item" onclick="nav(this,'settings','Settings')">
            <div class="nav-item-inner">
                <svg viewBox="0 0 16 16" stroke-width="1.5">
                    <circle cx="8" cy="8" r="2.2"/>
                    <path d="M8 1.5v1.8M8 12.7v1.8M1.5 8h1.8M12.7 8h1.8M3.4 3.4l1.3 1.3M11.3 11.3l1.3 1.3M3.4 12.6l1.3-1.3M11.3 4.7l1.3-1.3"/>
                </svg>
                Settings
            </div>
        </div>
    </nav>
    <div class="sidebar-bottom">
        <div class="theme-toggle" onclick="toggleTheme()">
            <span id="theme-label">Dark mode</span>
            <div class="toggle-track" id="toggle-track">
                <div class="toggle-thumb"></div>
            </div>
        </div>
        <button class="sb-btn" onclick="location.reload()">Refresh</button>
        <button class="sb-btn secondary" onclick="clearChat()">Clear Chat</button>
    </div>
</aside>

<div class="main">
    <div class="topbar">
        <span class="tb-logo">VulnSentinel</span>
        <span class="tb-sep">/</span>
        <span class="tb-page" id="tbTitle">Detection Feed</span>
        <div class="tb-spacer"></div>
        <div class="status-pill">
            <div class="led"></div>
            Pipeline online
        </div>
    </div>

    <div class="page active" id="page-analysis">
        <div class="hero">
            <div class="hero-label">Security Dashboard</div>
            <div class="hero-title">Detection Feed</div>
        </div>

        <div class="stats-row">
            <div class="stat">
                <div class="stat-label">Total Scans</div>
                <div class="stat-num">{{ reports|length }}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Critical</div>
                <div class="stat-num crit">{{ reports|selectattr('risk_level','eq','critical')|list|length }}</div>
            </div>
            <div class="stat">
                <div class="stat-label">High</div>
                <div class="stat-num high">{{ reports|selectattr('risk_level','eq','high')|list|length }}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Safe</div>
                <div class="stat-num safe">{{ reports|selectattr('risk_level','eq','low')|list|length }}</div>
            </div>
        </div>

        <div class="sec-hd">
            <span class="sec-label">All analyzed files</span>
            <span class="sec-count">{{ reports|length }} results</span>
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
                            <button class="toggle-btn" onclick="toggleSummary(this)">View summary</button>
                        </div>
                        <div class="rcard-right">
                            <div class="score {{ lvl }}">{{ score }}<span class="den">/10</span></div>
                            <a href="/download/{{ r.report_file }}" class="dl-btn">Export JSON</a>
                        </div>
                    </div>
                </div>
                <div class="summary-panel">
                    <div style="margin-bottom:12px">{{ summary }}</div>
                    {% if r.signal_scores is defined %}
                    <div class="signal-grid">
                        <div class="signal-box">
                            <div class="signal-label">Rules Engine</div>
                            <div class="signal-val">{{ r.signal_scores.rules_score }}<span class="den">/10</span></div>
                            <div class="signal-sub">Deterministic</div>
                        </div>
                        <div class="signal-box">
                            <div class="signal-label">LLM Score</div>
                            <div class="signal-val">{{ r.signal_scores.llm_score }}<span class="den">/10</span></div>
                            <div class="signal-sub">Conf: {{ r.signal_scores.llm_confidence }}/10</div>
                        </div>
                        <div class="signal-box">
                            <div class="signal-label">Semgrep</div>
                            <div class="signal-val">{{ r.signal_scores.semgrep_count }}<span class="den"> hits</span></div>
                            <div class="signal-sub">Pattern match</div>
                        </div>
                        <div class="signal-box">
                            <div class="signal-label">Sandbox</div>
                            <div class="signal-val" style="{% if r.signal_scores.sandbox_threat %}color:var(--red){% else %}color:var(--green){% endif %}">
                                {% if not r.signal_scores.sandbox_ran %}—{% elif r.signal_scores.sandbox_threat %}THREAT{% else %}CLEAN{% endif %}
                            </div>
                            <div class="signal-sub">Ground truth</div>
                        </div>
                    </div>
                    {% if r.decision is defined and r.decision.signals is defined %}
                    <div style="margin-top:12px;padding:12px 16px;background:var(--bg);border:1px solid var(--border);border-radius:8px">
                        <div style="font-family:'Inter',sans-serif;font-size:10px;font-weight:600;letter-spacing:1.8px;text-transform:uppercase;color:var(--gray-lo);margin-bottom:8px">Vote Breakdown</div>
                        {% for sig in r.decision.signals %}
                        <div style="font-family:'Inter',sans-serif;font-size:12px;color:var(--gray-mid);margin-bottom:3px">· {{ sig }}</div>
                        {% endfor %}
                        <div style="margin-top:8px;font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;color:var(--black)">
                            → {{ r.decision.final_action }} <span style="font-weight:400;color:var(--gray-mid)">({{ r.decision.confidence }} confidence)</span>
                        </div>
                    </div>
                    {% endif %}
                    {% endif %}
                </div>
                <div class="rcard-foot">
                    <span class="ts">{{ r.timestamp }}</span>
                </div>
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

    <div class="page" id="page-chat">
        <div class="chat-hd">
            <div class="chat-hd-title">AI Assistant</div>
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
            <div class="input-hint">Enter to send · Shift+Enter for new line</div>
        </div>
    </div>

    <div class="page" id="page-settings">
        <div class="hero">
            <div class="hero-label">System</div>
            <div class="hero-title">Settings</div>
        </div>
        <div class="sec-hd" style="margin-bottom:16px">
            <span class="sec-label">Pipeline configuration</span>
        </div>
        <div class="settings-list">
            <div class="srow"><span class="skey">LLM Model</span><span class="sval">mistral:7b</span></div>
            <div class="srow"><span class="skey">Ollama URL</span><span class="sval">http://localhost:11434</span></div>
            <div class="srow"><span class="skey">Risk Threshold</span><span class="sval">6 / 10</span></div>
            <div class="srow"><span class="skey">Sandbox Timeout</span><span class="sval">30s</span></div>
            <div class="srow"><span class="skey">Sandbox Memory</span><span class="sval">512m</span></div>
            <div class="srow"><span class="skey">Dashboard Port</span><span class="sval">5000</span></div>
            <div class="srow"><span class="skey">Inference</span><span class="sval">CPU — no GPU required</span></div>
        </div>
    </div>
</div>

<script>
const html = document.documentElement;
const track = document.getElementById('toggle-track');
const label = document.getElementById('theme-label');
const faviconLink = document.getElementById('favicon-link');

function buildFavicon(color) {
    const enc = encodeURIComponent(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">' +
        '<path d="M16 2L3 8v9.5C3 25 8.5 30.8 16 32.5 23.5 30.8 29 25 29 17.5V8L16 2z" fill="' + color + '"/>' +
        '</svg>'
    );
    faviconLink.href = 'data:image/svg+xml,' + enc;
}

function applyTheme(dark) {
    html.setAttribute('data-theme', dark ? 'dark' : 'light');
    track.classList.toggle('on', dark);
    label.textContent = dark ? 'Light mode' : 'Dark mode';
    buildFavicon(dark ? '#f0f0ee' : '#0a0a0a');
    localStorage.setItem('vs-theme', dark ? 'dark' : 'light');
}

function toggleTheme() {
    applyTheme(html.getAttribute('data-theme') !== 'dark');
}

(function() {
    const saved = localStorage.getItem('vs-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(saved ? saved === 'dark' : prefersDark);
})();

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
    btn.textContent = open ? 'View summary' : 'Hide summary';
}

const msgsEl = document.getElementById('chatMsgs');
function grow(el) { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 120) + 'px'; }
function onKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }
function bottom() { msgsEl.scrollTop = msgsEl.scrollHeight; }

function addMsg(role, html_content) {
    const d = document.createElement('div');
    d.className = 'msg ' + role;
    d.innerHTML =
        '<div class="av">' + (role === 'assistant' ? 'VS' : 'ME') + '</div>' +
        '<div class="msg-body">' +
        '<div class="msg-role">' + (role === 'assistant' ? 'Assistant' : 'You') + '</div>' +
        '<div class="bubble">' + html_content + '</div>' +
        '</div>';
    msgsEl.appendChild(d);
    bottom();
    return d.querySelector('.bubble');
}

function showTyping() {
    const d = document.createElement('div');
    d.className = 'msg assistant'; d.id = 'typing';
    d.innerHTML =
        '<div class="av">VS</div>' +
        '<div class="msg-body">' +
        '<div class="msg-role">Assistant</div>' +
        '<div class="bubble"><div class="typing">' +
        '<div class="tdot"></div><div class="tdot"></div><div class="tdot"></div>' +
        '</div></div></div>';
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
    msgsEl.innerHTML =
        '<div class="msg assistant">' +
        '<div class="av">VS</div>' +
        '<div class="msg-body">' +
        '<div class="msg-role">Assistant</div>' +
        '<div class="bubble">Chat cleared. Ready when you are.</div>' +
        '</div></div>';
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