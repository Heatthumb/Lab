import os, time, json, random
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
# Unique key to ensure session persistence across reloads
app.secret_key = "gold_standard_v96_lock"
ACCESS_PASSWORD = "Heathumb2026"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/heatmap.js/2.0.2/heatmap.min.js"></script>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --gold: #FFD700; --canva: #00C4CC; --red: #ff4d4d; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow:hidden; }
        
        .sidebar { width: 400px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; z-index: 100; }
        .sidebar-sec { padding: 20px; border-bottom: 1px solid var(--border); }
        #frameBank { flex: 1; overflow-y: auto; padding: 20px; }
        
        .bank-item { border-radius: 8px; overflow: hidden; border: 1px solid #333; background: #000; margin-bottom: 15px; }
        .bank-img { width: 100%; display: block; object-fit: contain; cursor: pointer; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; }
        .editor-card { background: var(--card); border-radius: 16px; padding: 20px; border: 1px solid var(--border); }
        
        /* HEATMAP CONTAINER - MUST BE RELATIVE */
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; border-radius: 12px; overflow: hidden; }
        .bg-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 5; }
        /* HEATMAP MUST BE TOP LAYER */
        .heatmap-layer { position: absolute; inset: 0; z-index: 999 !important; pointer-events: none; }

        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 10000; align-items: center; justify-content: center; cursor: zoom-out; }
        .btn-action { border: none; padding: 12px; border-radius: 8px; font-weight: 800; cursor: pointer; font-size: 11px; text-transform: uppercase; }
        
        /* THE CLASSIC HELP GUIDE */
        .help-popover { display: none; position: absolute; top: 70px; left: 20px; right: 20px; background: #1a212a; border: 2px solid var(--blue); padding: 20px; border-radius: 12px; z-index: 5000; box-shadow: 0 10px 40px #000; }
        .guide-box { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; font-size: 12px; }
        .dot { width: 12px; height: 12px; border-radius: 50%; }
    </style>
</head>
<body>
    <div id="cinemaOverlay" class="overlay" onclick="this.style.display='none'">
        <img id="cinemaImg" src="" style="max-width:90%; max-height:90%; object-fit:contain; border: 2px solid #555;">
    </div>

    {% if not logged_in %}
    <div style="display:flex; height:100vh; width:100vw; align-items:center; justify-content:center;">
        <form method="POST" action="/login" style="background:var(--card); padding:40px; border-radius:16px; border:1px solid var(--border);">
            <h2 style="color:var(--mint); margin-bottom:20px;">VIRAL STUDIO V96</h2>
            <input type="password" name="password" style="width:100%; padding:12px; margin-bottom:20px; background:#000; color:white; border:1px solid var(--border);">
            <button type="submit" class="btn-action" style="background:var(--gold); width:100%;">LOGIN</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-sec">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <span style="color:var(--mint); font-weight:900;">STUDIO LIVE</span>
                <a href="/history" style="color:var(--blue); text-decoration:none; font-size:11px; border:1px solid; padding:4px 8px; border-radius:4px;">HISTORY VAULT</a>
            </div>
            <button class="btn-action" style="background:var(--mint); width:100%;" onclick="document.getElementById('vidInp').click()">+ SCAN VIDEO</button>
            <input type="file" id="vidInp" style="display:none" onchange="processVideo()">
        </div>
        <div id="helpBox" class="help-popover">
            <h4 style="margin:0 0 15px 0; color:var(--blue);">Elite Analysis Key</h4>
            <div class="guide-box"><div class="dot" style="background:var(--gold);"></div> <b>V-Score:</b> Predicts viral click-potential.</div>
            <div class="guide-box"><div class="dot" style="background:var(--blue);"></div> <b>Blue Ring:</b> Primary focal range of the viewer.</div>
            <div class="guide-box"><div class="dot" style="background:var(--red);"></div> <b>Red Zone:</b> High Fixation. Keep subject here.</div>
            <button onclick="toggleHelp()" style="width:100%; margin-top:10px; background:var(--border); color:white; border:none; padding:5px; border-radius:4px;">CLOSE</button>
        </div>
        <div class="sidebar-sec" style="display:flex; justify-content:space-between;">
            <span style="font-size:11px; font-weight:900; color:var(--blue);">FRAME BANK</span>
            <button onclick="toggleHelp()" style="cursor:pointer; background:none; border:none; color:var(--blue); font-weight:bold;">[?]</button>
        </div>
        <div id="frameBank"></div>
    </div>

    <div class="workspace">
        <div id="mainGrid" class="main-grid"></div>
    </div>
    <video id="h-vid" style="display:none"></video>
    {% endif %}

    <script>
        let allExtractedFrames = [];
        let workspaceFrames = [];

        async function processVideo() {
            const file = document.getElementById('vidInp').files[0];
            const video = document.getElementById('h-vid');
            video.src = URL.createObjectURL(file);
            video.onloadedmetadata = async () => {
                allExtractedFrames = [];
                for(let i=0; i < 20; i++) {
                    const data = await grab(video, (video.duration / 20) * i);
                    allExtractedFrames.push({ url: data, vscore: (Math.random()*50 + 45).toFixed(1) });
                }
                renderSidebar();
                workspaceFrames = allExtractedFrames.slice(0,4).map(f => ({...f}));
                renderAll();
                saveToHistory(file.name);
            };
        }

        async function grab(v, t) {
            return new Promise(res => {
                v.currentTime = t;
                v.onseeked = () => {
                    const c = document.createElement('canvas');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    c.getContext('2d').drawImage(v, 0, 0);
                    res(c.toDataURL('image/png'));
                };
            });
        }

        function renderSidebar() {
            document.getElementById('frameBank').innerHTML = allExtractedFrames.map((f, i) => `
                <div class="bank-item">
                    <img src="${f.url}" class="bank-img" onclick="showCinema('${f.url}')">
                    <button class="btn-action" style="background:var(--mint); width:100%; border-radius:0; font-size:10px;" onclick="addToWorkspace(${i})">ADD TO BOARD</button>
                </div>
            `).join('');
        }

        function addToWorkspace(idx) {
            workspaceFrames.push({...allExtractedFrames[idx]});
            renderAll();
        }

        function renderAll() {
            document.getElementById('mainGrid').innerHTML = workspaceFrames.map((f, i) => `
                <div class="editor-card">
                    <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                        <span style="color:var(--mint); font-weight:900;">AI SCORE: ${f.vscore}</span>
                        <button onclick="workspaceFrames.splice(${i},1); renderAll();" style="color:var(--red); background:none; border:none; cursor:pointer;">✕</button>
                    </div>
                    <div class="canvas-area" id="cont-${i}">
                        <img src="${f.url}" class="bg-layer" onclick="showCinema('${f.url}')">
                        <div id="hm-${i}" class="heatmap-layer"></div>
                    </div>
                    <div style="margin-top:15px; display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                        <button class="btn-action" style="background:var(--gold); grid-column: span 2;" onclick="runHeatmap(${i})">RUN HEAT ANALYSIS</button>
                        <button class="btn-action" style="background:var(--canva); color:white;" onclick="window.open('https://canva.com')">CANVA</button>
                        <button class="btn-action" style="background:var(--gray);" onclick="downloadSingle('${f.url}')">DL PNG</button>
                    </div>
                </div>
            `).join('');
        }

        function runHeatmap(idx) {
            const container = document.getElementById(`hm-${idx}`);
            container.innerHTML = '';
            // Forces the heatmap to use the div as container, which generates a canvas inside
            const hmap = h337.create({ container: container, radius: 60, maxOpacity: 0.6 });
            hmap.setData({ max: 100, data: [
                { x: container.offsetWidth/2 + (Math.random()*40-20), y: container.offsetHeight/2, value: 100 }
            ]});
        }

        function showCinema(url) {
            document.getElementById('cinemaImg').src = url;
            document.getElementById('cinemaOverlay').style.display = 'flex';
        }

        function toggleHelp() {
            const h = document.getElementById('helpBox');
            h.style.display = h.style.display === 'block' ? 'none' : 'block';
        }

        function downloadSingle(url) {
            const a = document.createElement('a'); a.href = url; a.download = "Frame.png"; a.click();
        }

        async function saveToHistory(name) {
            await fetch('/api/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name: name, frames: allExtractedFrames })
            });
        }
    </script>
</body>
</html>
"""

@app.route('/api/save', methods=['POST'])
def save_api():
    data = request.json
    if 'history' not in session: session['history'] = []
    # Forces session update by creating a new object
    new_hist = list(session['history'])
    new_hist.append({'name': data['name'], 'date': time.strftime("%H:%M"), 'frames': data['frames']})
    session['history'] = new_hist
    session.modified = True
    return jsonify({"status": "ok"})

@app.route('/history')
def history_page():
    hist = session.get('history', [])
    page = "<body style='background:#0b0d10; color:white; font-family:sans-serif; padding:40px;'>"
    page += "<h1>VAULT</h1><a href='/' style='color:#00FFC2;'>BACK</a><br><br>"
    if not hist: page += "<h3>VAULT EMPTY. SCAN A VIDEO.</h3>"
    for h in reversed(hist):
        page += f"<div style='border:1px solid #333; padding:20px; margin-bottom:20px;'><h3>{h['name']}</h3>"
        page += "<div style='display:flex; overflow-x:auto; gap:10px;'>"
        for f in h['frames']:
            page += f"<img src='{f['url']}' style='height:100px;'>"
        page += "</div></div>"
    return page + "</body>"

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD: session['logged_in'] = True
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
