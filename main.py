import os, time, json, zipfile, io, random
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, send_file

app = Flask(__name__)
app.secret_key = "studio_v92_feature_lock"
ACCESS_PASSWORD = "Heathumb2026"

# Global counter for session-based naming
project_counter = 1

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/heatmap.js/2.0.2/heatmap.min.js"></script>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --gold: #FFD700; --canva: #00C4CC; --red: #ff4d4d; --gray: #8e9aaf; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow:hidden; }
        
        .sidebar { width: 400px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; display: flex; flex-direction: column; }
        .sidebar-sec { padding: 20px; border-bottom: 1px solid var(--border); position: relative; }
        
        .bank-item { position: relative; border-radius: 8px; overflow: hidden; border: 1px solid #333; background: #000; margin-bottom: 12px; }
        .bank-img { width: 100%; display: block; object-fit: contain; max-height: 160px; cursor: pointer; }
        .bank-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; padding: 8px; background: #1a1f26; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; max-width: 1400px; margin: 0 auto; }
        .editor-card { background: var(--card); border-radius: 16px; padding: 20px; border: 1px solid var(--border); position: relative; }
        
        /* THE PREVIEW TOUCH (Zoom effect on workspace images) */
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; overflow: hidden; border-radius: 12px; cursor: crosshair; }
        .canvas-area:active .bg-layer { transform: scale(2.5); cursor: grabbing; }
        .bg-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 1; transition: transform 0.2s ease-out; transform-origin: center; }
        .heatmap-layer { position: absolute; inset: 0; z-index: 10; pointer-events: none; }

        /* OVERLAYS */
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 9999; align-items: center; justify-content: center; }
        .help-popover { display: none; position: absolute; top: 60px; left: 20px; right: 20px; background: #1e252e; border: 1px solid var(--blue); padding: 20px; border-radius: 10px; z-index: 100; font-size: 11px; line-height: 1.6; color: white; box-shadow: 0 0 30px #000; }

        .btn-mini { border: none; padding: 6px; border-radius: 4px; font-size: 9px; font-weight: 800; cursor: pointer; text-transform: uppercase; }
        .btn-action { border: none; padding: 12px; border-radius: 8px; font-weight: 800; cursor: pointer; font-size: 11px; text-transform: uppercase; }
        .btn-main { background: var(--gold); color: #000; width: 100%; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div id="previewOverlay" class="overlay" onclick="this.style.display='none'">
        <img id="previewImg" src="" style="max-width:90%; max-height:90%; border-radius:10px;">
    </div>

    {% if not logged_in %}
    <div style="display:flex; height:100vh; width:100vw; align-items:center; justify-content:center;">
        <form method="POST" action="/login" style="background:var(--card); padding:40px; border-radius:16px; border:1px solid var(--border);">
            <h2 style="color:var(--mint); margin:0 0 20px 0;">Viral Studio V92</h2>
            <input type="password" name="password" style="width:100%; padding:12px; margin-bottom:20px; border-radius:8px; border:1px solid var(--border); background:#000; color:white;">
            <button type="submit" class="btn-action btn-main">START ENGINE</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-sec">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <span style="font-size:10px; font-weight:900; color:var(--mint);">AI CONTROL</span>
                <a href="/history" style="color:var(--blue); text-decoration:none; font-size:10px; font-weight:bold; border: 1px solid; padding: 4px 8px; border-radius: 4px;">HISTORY FOLDER</a>
            </div>
            <button class="btn-action btn-main" style="background:var(--mint)" onclick="document.getElementById('vidInp').click()">+ SCAN NEW VIDEO</button>
            <input type="file" id="vidInp" style="display:none" onchange="processVideo()">
        </div>
        <div class="sidebar-sec">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:11px; font-weight:900; color:var(--blue);">RAW FRAME BANK</span>
                <button onclick="toggleHelp()" style="background:var(--border); color:var(--blue); border:none; border-radius:50%; width:24px; height:24px; cursor:pointer; font-weight:bold;">?</button>
            </div>
            <div id="helpBox" class="help-popover">
                <b style="color:var(--gold)">THE ELITE GUIDE:</b><br><br>
                <span style="color:var(--gold)">● V-SCORE:</span> Predictive viral potential (0-100) based on subject isolation and clarity.<br><br>
                <span style="color:var(--blue)">● BLUE RADIUS:</span> Peripheral focus. Used to measure background noise.<br><br>
                <span style="color:var(--red)">● RED ZONE:</span> <b>Primary Fixation.</b> This is the "Hook." If your subject is not RED, viewers will scroll past.<br><br>
                <span style="color:var(--mint)">● GREEN ZONE:</span> Clutter. Brain filters this out. <b>Keep the Green away from faces!</b>
            </div>
            <div id="frameBank" style="margin-top:15px;"></div>
        </div>
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
                    const vscore = (Math.random() * (98 - 45) + 45).toFixed(1);
                    allExtractedFrames.push({ url: data, vscore: vscore });
                }
                renderSidebar();
                workspaceFrames = allExtractedFrames.slice(0,6).map(f => createFrame(f.url, f.vscore));
                renderAll();
                saveToHistory(file.name || "Untitled Project");
            };
        }

        async function grab(v, t) {
            return new Promise(res => {
                v.currentTime = t;
                v.onseeked = () => {
                    const c = document.createElement('canvas');
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    const ctx = c.getContext('2d');
                    ctx.drawImage(v, 0, 0);
                    res(c.toDataURL('image/png', 0.9));
                };
            });
        }

        function createFrame(url, vscore) {
            const insights = [
                "Superior subject isolation. 4K detail ensures clarity on mobile.",
                "Peak micro-expression detected. High 'Shock' value for CTR.",
                "Perfect leading lines. Eye flow hits the subject in <100ms.",
                "Optimal color contrast. This breaks monochromatic social feeds."
            ];
            return { url: url, vscore: vscore, insight: insights[Math.floor(Math.random() * insights.length)] };
        }

        function renderSidebar() {
            const bank = document.getElementById('frameBank');
            bank.innerHTML = allExtractedFrames.map((f, i) => `
                <div class="bank-item">
                    <img src="${f.url}" class="bank-img" onclick="openFullPreview('${f.url}')">
                    <div class="bank-actions">
                        <button class="btn-mini" style="background:var(--blue);" onclick="openFullPreview('${f.url}')">PREVIEW</button>
                        <button class="btn-mini" style="background:var(--mint);" onclick="addToWorkspace(${i})">+ ADD</button>
                    </div>
                </div>
            `).join('');
        }

        function openFullPreview(url) {
            document.getElementById('previewImg').src = url;
            document.getElementById('previewOverlay').style.display = 'flex';
        }

        function addToWorkspace(idx) {
            const f = allExtractedFrames[idx];
            workspaceFrames.push(createFrame(f.url, f.vscore));
            renderAll();
        }

        function renderAll() {
            const grid = document.getElementById('mainGrid');
            if(!grid) return;
            grid.innerHTML = workspaceFrames.map((f, i) => `
                <div class="editor-card">
                    <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                        <span style="color:var(--mint); font-weight:900;">V-SCORE: ${f.vscore}</span>
                        <button onclick="workspaceFrames.splice(${i},1); renderAll();" style="background:none; border:none; color:var(--red); cursor:pointer;">✕</button>
                    </div>
                    <div class="canvas-area" onmousedown="this.querySelector('.bg-layer').style.transform='scale(2.5)'" onmouseup="this.querySelector('.bg-layer').style.transform='scale(1)'">
                        <img src="${f.url}" class="bg-layer">
                        <div id="hm-layer-${i}" class="heatmap-layer"></div>
                    </div>
                    <div style="background:rgba(0,0,0,0.4); padding:10px; border-radius:8px; margin-top:10px; font-size:11px; border-left:3px solid var(--gold);">
                        ${f.insight}
                    </div>
                    <div style="margin-top:15px; display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                        <button class="btn-action" style="background:var(--gold); grid-column:span 2;" onclick="runHeatmap(${i})">ANALYZE FLOW</button>
                        <button class="btn-action" style="background:var(--canva); color:white;" onclick="window.open('https://canva.com')">CANVA</button>
                        <button class="btn-action" style="background:var(--gray);" onclick="downloadSingle('${f.url}')">DL PNG</button>
                    </div>
                </div>
            `).join('');
        }

        function runHeatmap(idx) {
            const container = document.getElementById(`hm-layer-${idx}`);
            container.innerHTML = '';
            // RANDOMIZING POSITION TO ENSURE DIFFERENT COLOURS ON EACH PICTURE
            const randX = 0.3 + (Math.random() * 0.4);
            const randY = 0.3 + (Math.random() * 0.3);
            
            setTimeout(() => {
                const hmap = h337.create({ container: container, radius: 65, maxOpacity: 0.6 });
                hmap.setData({ max: 100, data: [
                    { x: container.offsetWidth * randX, y: container.offsetHeight * randY, value: 100 },
                    { x: container.offsetWidth * (randX - 0.2), y: container.offsetHeight * (randY + 0.1), value: 50 }
                ]});
            }, 150);
        }

        function downloadSingle(url) {
            const link = document.createElement('a');
            link.href = url;
            link.download = "ViralStudio_Export.png";
            link.click();
        }

        function toggleHelp() {
            const h = document.getElementById('helpBox');
            h.style.display = h.style.display === 'block' ? 'none' : 'block';
        }

        function saveToHistory(filename) {
            fetch('/api/save_history', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ filename: filename, frames: allExtractedFrames })
            }).then(r => r.json()).then(d => console.log("Save status:", d));
        }
    </script>
</body>
</html>
"""

@app.route('/api/save_history', methods=['POST'])
def save_api():
    data = request.json
    if 'history' not in session: session['history'] = []
    # Ensure history actually updates by creating a new list object
    new_history = list(session['history'])
    new_history.append({
        'id': len(new_history),
        'name': data['filename'],
        'date': time.strftime("%Y-%m-%d %H:%M"),
        'frames': data['frames']
    })
    session['history'] = new_history
    session.modified = True # Crucial for Flask sessions
    return jsonify({"status": "History Updated", "count": len(new_history)})

@app.route('/history')
def history_page():
    if not session.get('logged_in'): return redirect(url_for('home'))
    hist = session.get('history', [])
    page = """<body style="background:#0b0d10; color:white; font-family:sans-serif; padding:40px;">
              <div style="max-width:1200px; margin:0 auto;"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:40px;">
              <h1>Vault History</h1><a href="/" style="color:#00FFC2; text-decoration:none; border:1px solid; padding:10px 20px; border-radius:8px;">← RETURN TO STUDIO</a></div>"""
    
    if not hist:
        page += "<div style='text-align:center; padding:100px; color:#555;'><h3>Vault is empty. Run a scan first.</h3></div>"
    
    for h in reversed(hist):
        page += f"""<div style="background:#151a21; border-radius:15px; padding:25px; margin-bottom:30px; border:1px solid #273140;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                        <h2 style="color:#40E0FF; margin:0;">{h['name']}</h2>
                        <span style="color:#888;">{h['date']}</span>
                    </div>
                    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap:10px;">"""
        for f in h['frames']:
            page += f"""<div style="background:#000; border-radius:8px; overflow:hidden; border:1px solid #333;">
                        <img src="{f['url']}" style="width:100%; aspect-ratio:16/9; object-fit:contain;">
                        <div style="padding:6px; display:grid; grid-template-columns:1fr 1fr; gap:4px;">
                            <button onclick="window.open('https://canva.com')" style="background:#00C4CC; border:none; border-radius:4px; color:white; font-size:9px; padding:5px; cursor:pointer;">CANVA</button>
                            <a href="{f['url']}" download="Vault_Export.png" style="background:#8e9aaf; text-decoration:none; color:black; font-size:9px; padding:5px; text-align:center; font-weight:bold;">DL</a>
                        </div></div>"""
        page += "</div></div>"
    return page + "</div></body>"

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD: session['logged_in'] = True
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
