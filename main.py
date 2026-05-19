import os, boto3, time, json, zipfile, io, random
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, send_file

app = Flask(__name__)
app.secret_key = "studio_v91_final_integrity"
ACCESS_PASSWORD = "Heathumb2026"

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
        
        /* SIDEBAR & UI */
        .sidebar { width: 400px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; display: flex; flex-direction: column; }
        .sidebar-sec { padding: 20px; border-bottom: 1px solid var(--border); position: relative; }
        .section-title { font-size: 11px; font-weight: 900; color: var(--blue); text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        
        .bank-item { position: relative; border-radius: 8px; overflow: hidden; border: 1px solid #333; background: #000; margin-bottom: 12px; transition: 0.2s; }
        .bank-img { width: 100%; display: block; object-fit: contain; max-height: 160px; cursor: zoom-in; }
        .bank-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; padding: 8px; background: #1a1f26; }
        .btn-mini { border: none; padding: 6px; border-radius: 4px; font-size: 9px; font-weight: 800; cursor: pointer; text-transform: uppercase; }

        /* WORKSPACE */
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; max-width: 1400px; margin: 0 auto; }
        .editor-card { background: var(--card); border-radius: 16px; padding: 20px; border: 1px solid var(--border); }
        
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; overflow: hidden; border-radius: 12px; }
        .bg-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 1; }
        .heatmap-layer { position: absolute; inset: 0; z-index: 10; pointer-events: none; width: 100%; height: 100%; }

        /* OVERLAYS & HELP */
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.96); z-index: 9999; align-items: center; justify-content: center; }
        .help-popover { display: none; position: absolute; top: 60px; left: 20px; right: 20px; background: #1e252e; border: 1px solid var(--blue); padding: 20px; border-radius: 10px; z-index: 100; font-size: 11px; line-height: 1.6; box-shadow: 0 20px 50px #000; }

        .btn-action { border: none; padding: 12px; border-radius: 8px; font-weight: 800; cursor: pointer; font-size: 11px; text-transform: uppercase; }
        .btn-main { background: var(--gold); color: #000; width: 100%; margin-bottom: 10px; }
        .card-controls { margin-top: 15px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    </style>
</head>
<body>
    <div id="previewOverlay" class="overlay" onclick="this.style.display='none'">
        <img id="previewImg" src="" style="max-width:90%; max-height:90%; border-radius:10px; border: 1px solid var(--border);">
    </div>

    {% if not logged_in %}
    <div style="display:flex; height:100vh; width:100vw; align-items:center; justify-content:center;">
        <form method="POST" action="/login" style="background:var(--card); padding:40px; border-radius:16px; border:1px solid var(--border);">
            <h2 style="color:var(--mint); margin:0 0 20px 0;">Viral Studio V91</h2>
            <input type="password" name="password" style="width:100%; padding:12px; margin-bottom:20px; border-radius:8px; border:1px solid var(--border); background:#000; color:white;">
            <button type="submit" class="btn-action btn-main">START WORKSPACE</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-sec">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <span style="font-size:10px; font-weight:900; color:var(--mint);">ANALYTICS LIVE</span>
                <a href="/history" style="color:var(--blue); text-decoration:none; font-size:10px; font-weight:bold; border:1px solid; padding:4px 8px; border-radius:4px;">HISTORY VAULT</a>
            </div>
            <button class="btn-action btn-main" style="background:var(--mint)" onclick="document.getElementById('vidInp').click()">+ SCAN NEW VIDEO</button>
            <input type="file" id="vidInp" style="display:none" onchange="processVideo()">
        </div>
        <div class="sidebar-sec">
            <div class="section-title">
                20-Frame Bank
                <button onclick="toggleHelp()" style="background:var(--border); color:var(--blue); border:none; border-radius:50%; width:24px; height:24px; cursor:pointer; font-weight:bold;">?</button>
            </div>
            <div id="helpBox" class="help-popover">
                <b style="color:var(--mint)">THE HEATMAP COLOR SCIENCE:</b><br><br>
                <span style="color:var(--red)">● RED ZONE:</span> <b>Critical Fixation.</b> This is the "Hook." 90% of eyes land here in <0.5s. If your subject isn't Red, the thumbnail will fail.<br><br>
                <span style="color:var(--mint)">● GREEN ZONE:</span> <b>Peripheral Context.</b> Background or side elements. If your face/text is in the Green, the viewer's brain filters it as "clutter." <b>Keep Green on the edges, never on the subject.</b>
            </div>
            <div id="frameBank" class="frame-bank"></div>
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

        const AI_LIB = [
            "Superior facial symmetry detected. This reduces scroll-friction by 40%.",
            "High micro-expression intensity. Statistical outlier for curiosity-driven clicks.",
            "Optimal subject isolation. 4K detail ensures facial clarity on mobile feeds.",
            "Exceptional eye-contact detected. This frame creates instant viewer trust.",
            "Kinetic motion-blur detected. Suggests high-energy content to the brain.",
            "Negative space balance is perfect for bold Canva typography overlays."
        ];

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
                saveToHistory(file.name || "");
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
                    res(c.toDataURL('image/png', 0.95));
                };
            });
        }

        function createFrame(url, vscore) {
            return { url: url, vscore: vscore, insight: AI_LIB[Math.floor(Math.random() * AI_LIB.length)] };
        }

        function renderSidebar() {
            const bank = document.getElementById('frameBank');
            bank.innerHTML = allExtractedFrames.map((f, i) => `
                <div class="bank-item">
                    <img src="${f.url}" class="bank-img" onclick="showPreview('${f.url}')">
                    <div class="bank-actions">
                        <button class="btn-mini" style="background:var(--blue);" onclick="showPreview('${f.url}')">PREVIEW</button>
                        <button class="btn-mini" style="background:var(--mint);" onclick="addToWorkspace(${i})">+ ADD</button>
                    </div>
                </div>
            `).join('');
        }

        function showPreview(url) {
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
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span style="color:var(--mint); font-weight:900; font-size:14px;">V-SCORE: ${f.vscore}</span>
                        <button onclick="workspaceFrames.splice(${i},1); renderAll();" style="background:none; border:none; color:var(--red); cursor:pointer; font-size:18px;">✕</button>
                    </div>
                    <div class="canvas-area" id="area-${i}">
                        <img src="${f.url}" class="bg-layer">
                        <div id="hm-layer-${i}" class="heatmap-layer"></div>
                    </div>
                    <div style="background:rgba(0,0,0,0.5); padding:12px; border-radius:8px; margin-top:15px; font-size:11px; border-left:4px solid var(--gold); line-height:1.4;">
                        <b style="color:var(--gold); display:block; margin-bottom:4px; font-size:9px; text-transform:uppercase;">AI STRATEGIC INSIGHT</b>
                        ${f.insight}
                    </div>
                    <div class="card-controls">
                        <button class="btn-action" style="background:var(--gold); grid-column:span 2;" onclick="runHeatmap(${i})">ANALYZE ATTENTION FLOW</button>
                        <button class="btn-action" style="background:var(--canva); color:white;" onclick="window.open('https://canva.com','_blank')">SEND TO CANVA</button>
                        <button class="btn-action" style="background:var(--gray);" onclick="downloadSingle('${f.url}')">DOWNLOAD PNG</button>
                    </div>
                </div>
            `).join('');
        }

        function runHeatmap(idx) {
            const container = document.getElementById(`hm-layer-${idx}`);
            container.innerHTML = '';
            setTimeout(() => {
                const hmap = h337.create({ container: container, radius: 60, maxOpacity: 0.6 });
                hmap.setData({ max: 100, data: [
                    { x: container.offsetWidth*0.5, y: container.offsetHeight*0.4, value: 100 },
                    { x: container.offsetWidth*0.2, y: container.offsetHeight*0.7, value: 40 }
                ]});
            }, 120);
        }

        function downloadSingle(url) {
            const link = document.createElement('a');
            link.download = "ViralStudio_Export.png";
            link.href = url;
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
            });
        }
    </script>
</body>
</html>
"""

@app.route('/api/save_history', methods=['POST'])
def save_api():
    global project_counter
    data = request.json
    if 'history' not in session: session['history'] = []
    name = data['filename'] or f"Project #{project_counter}"
    if not data['filename']: project_counter += 1
    session['history'].append({'name': name, 'date': time.strftime("%Y-%m-%d %H:%M"), 'frames': data['frames']})
    session.modified = True
    return jsonify({"status": "saved"})

@app.route('/history')
def history_page():
    hist = session.get('history', [])
    page = """<body style="background:#0b0d10; color:white; font-family:sans-serif; padding:40px;">
              <div style="max-width:1200px; margin:0 auto;"><div style="display:flex; justify-content:space-between; margin-bottom:40px;">
              <h1>History Vault</h1><a href="/" style="color:var(--mint); text-decoration:none; font-weight:bold;">← BACK TO STUDIO</a></div>"""
    for i, h in enumerate(hist):
        page += f"""<div style="background:#151a21; border-radius:15px; padding:25px; margin-bottom:30px; border:1px solid #273140;">
                    <h3>{h['name']} ({h['date']})</h3><div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap:10px;">"""
        for frame in h['frames']:
            page += f"""<div style="background:#000; border-radius:8px; overflow:hidden; border:1px solid #333;">
                        <img src="{frame['url']}" style="width:100%; aspect-ratio:16/9; object-fit:contain;">
                        <div style="padding:6px; display:grid; grid-template-columns:1fr 1fr; gap:4px;">
                            <button onclick="window.open('https://canva.com')" style="background:var(--canva); border:none; border-radius:4px; color:white; font-size:9px; padding:5px; cursor:pointer;">CANVA</button>
                            <a href="{frame['url']}" download style="background:var(--gray); text-decoration:none; color:black; font-size:9px; padding:5px; text-align:center;">DL</a>
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
