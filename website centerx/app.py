from flask import Flask, jsonify, render_template_string
import threading
import os
import sys
import subprocess
import datetime

app = Flask(__name__)

# เก็บ process ของ bot
bot_process = None
bot_start_time = None
bot_status = "stopped"

def start_bot():
    global bot_process, bot_start_time, bot_status
    try:
        bot_process = subprocess.Popen(
            [sys.executable, "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        bot_start_time = datetime.datetime.utcnow()
        bot_status = "running"
    except Exception as e:
        bot_status = f"error: {e}"

HTML = """
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ULTIMATEX — Bot Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg: #050508;
    --surface: #0d0d14;
    --border: #1a1a2e;
    --accent: #7c3aed;
    --accent2: #06b6d4;
    --text: #e2e8f0;
    --muted: #475569;
    --green: #10b981;
    --red: #ef4444;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* animated grid bg */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(124,58,237,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(124,58,237,0.04) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
  }

  /* glow orbs */
  .orb {
    position: fixed;
    border-radius: 50%;
    filter: blur(120px);
    pointer-events: none;
    z-index: 0;
  }
  .orb-1 { width: 500px; height: 500px; background: rgba(124,58,237,0.12); top: -150px; left: -150px; }
  .orb-2 { width: 400px; height: 400px; background: rgba(6,182,212,0.08); bottom: -100px; right: -100px; }

  .container {
    position: relative;
    z-index: 1;
    max-width: 860px;
    margin: 0 auto;
    padding: 60px 24px;
  }

  /* header */
  .header {
    text-align: center;
    margin-bottom: 56px;
    animation: fadeUp 0.6s ease both;
  }

  .logo {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
  }
  .logo-icon {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
  }
  .logo-text {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 0.1em;
    background: linear-gradient(135deg, #a78bfa, var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  h1 {
    font-family: 'Syne', sans-serif;
    font-size: clamp(32px, 6vw, 52px);
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }
  h1 span {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .subtitle {
    margin-top: 12px;
    color: var(--muted);
    font-size: 14px;
    letter-spacing: 0.05em;
  }

  /* status card */
  .status-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 20px;
    animation: fadeUp 0.6s ease 0.1s both;
    position: relative;
    overflow: hidden;
  }
  .status-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
  }

  .status-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
  }
  .status-label {
    font-size: 11px;
    letter-spacing: 0.15em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .status-value {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 700;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 500;
    font-family: 'DM Mono', monospace;
  }
  .badge-running {
    background: rgba(16,185,129,0.15);
    border: 1px solid rgba(16,185,129,0.3);
    color: var(--green);
  }
  .badge-stopped {
    background: rgba(239,68,68,0.15);
    border: 1px solid rgba(239,68,68,0.3);
    color: var(--red);
  }
  .badge-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s ease infinite;
  }

  /* stats grid */
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
    animation: fadeUp 0.6s ease 0.2s both;
  }
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 22px;
  }
  .stat-label {
    font-size: 11px;
    letter-spacing: 0.12em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .stat-value {
    font-family: 'Syne', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: var(--text);
  }
  .stat-accent { color: var(--accent2); }

  /* log box */
  .log-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    animation: fadeUp 0.6s ease 0.3s both;
  }
  .log-title {
    font-size: 11px;
    letter-spacing: 0.15em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 14px;
  }
  .log-entries {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .log-entry {
    display: flex;
    gap: 10px;
    font-size: 12px;
    line-height: 1.6;
  }
  .log-time { color: var(--muted); min-width: 80px; }
  .log-msg { color: var(--text); }
  .log-msg.success { color: var(--green); }
  .log-msg.info { color: var(--accent2); }

  /* footer ping */
  .ping-bar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: var(--muted);
    animation: fadeUp 0.6s ease 0.4s both;
  }
  .ping-bar a {
    color: var(--accent2);
    text-decoration: none;
  }

  /* animations */
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
</style>
</head>
<body>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>

<div class="container">
  <div class="header">
    <div class="logo">
      <div class="logo-icon">🔑</div>
      <div class="logo-text">ULTIMATEX</div>
    </div>
    <h1>Bot <span>Dashboard</span></h1>
    <p class="subtitle">KeyAuth Discord Bot — Control Panel</p>
  </div>

  <!-- status -->
  <div class="status-card">
    <div class="status-row">
      <div>
        <div class="status-label">Bot Status</div>
        <div class="status-value" id="statusText">{{ status }}</div>
      </div>
      <div id="statusBadge">
        {% if status == 'running' %}
        <span class="badge badge-running"><span class="badge-dot"></span>Online</span>
        {% else %}
        <span class="badge badge-stopped"><span class="badge-dot"></span>Offline</span>
        {% endif %}
      </div>
    </div>
  </div>

  <!-- stats -->
  <div class="stats">
    <div class="stat-card">
      <div class="stat-label">App Name</div>
      <div class="stat-value stat-accent">{{ app_name }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Uptime</div>
      <div class="stat-value" id="uptimeVal">{{ uptime }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Server Time (UTC)</div>
      <div class="stat-value" id="serverTime">{{ now }}</div>
    </div>
  </div>

  <!-- log -->
  <div class="log-card">
    <div class="log-title">// System Log</div>
    <div class="log-entries">
      <div class="log-entry">
        <span class="log-time">{{ now }}</span>
        <span class="log-msg info">Server started — keep-alive active</span>
      </div>
      <div class="log-entry">
        <span class="log-time">{{ now }}</span>
        <span class="log-msg {% if status == 'running' %}success{% endif %}">
          Bot process: {{ status }}
        </span>
      </div>
    </div>
  </div>

  <!-- ping -->
  <div class="ping-bar">
    <span>Ping this URL every <strong>5 min</strong> to keep alive</span>
    <span id="currentUrl">—</span>
  </div>
</div>

<script>
  // show current URL
  document.getElementById('currentUrl').textContent = window.location.origin + '/ping';

  // live clock
  function updateClock() {
    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    const timeStr = pad(now.getUTCHours()) + ':' + pad(now.getUTCMinutes()) + ':' + pad(now.getUTCSeconds());
    document.getElementById('serverTime').textContent = timeStr + ' UTC';
  }
  setInterval(updateClock, 1000);
  updateClock();

  // auto-refresh status every 30s
  async function refreshStatus() {
    try {
      const r = await fetch('/status');
      const d = await r.json();
      document.getElementById('statusText').textContent = d.status;
      document.getElementById('uptimeVal').textContent = d.uptime;
      const badge = document.getElementById('statusBadge');
      badge.innerHTML = d.status === 'running'
        ? '<span class="badge badge-running"><span class="badge-dot"></span>Online</span>'
        : '<span class="badge badge-stopped"><span class="badge-dot"></span>Offline</span>';
    } catch(e) {}
  }
  setInterval(refreshStatus, 30000);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    now = datetime.datetime.utcnow().strftime("%H:%M:%S")
    uptime = "—"
    if bot_start_time:
        delta = datetime.datetime.utcnow() - bot_start_time
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        uptime = f"{h}h {m}m {s}s"
    return render_template_string(
        HTML,
        status=bot_status,
        app_name=os.getenv("KEYAUTH_APP_NAME", "ULTIMATEX"),
        uptime=uptime,
        now=now,
    )

@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "bot": bot_status})

@app.route("/status")
def status():
    uptime = "—"
    if bot_start_time:
        delta = datetime.datetime.utcnow() - bot_start_time
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        uptime = f"{h}h {m}m {s}s"
    return jsonify({"status": bot_status, "uptime": uptime})

if __name__ == "__main__":
    # เริ่ม bot ใน thread แยก
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)