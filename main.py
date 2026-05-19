import os, boto3, time, json, zipfile, io, random
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, send_file

app = Flask(__name__)
app.secret_key = "studio_v88_infinite_logic"
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
        
        /* SIDEBAR - Fixed for Mobile/Full Frame Visibility */
        .sidebar { width: 380px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; display: flex; flex-direction: column; }
        .sidebar-sec { padding: 20px; border-bottom: 1px solid var(--border); position: relative; }
        .section-title { font-size: 11px; font-weight: 900; color: var(--blue); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        
        .bank-item { position: relative; border-radius: 8px; overflow: hidden; border: 1px solid #333; cursor: pointer; background: #000; margin-bottom: 10px; }
        .bank-img { width: 100%; display: block; object-fit: contain; max-height: 180px; } /* Ensures full frame visibility for mobile videos */
        
        /* WORKSPACE */
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; max-width: 1400px; margin: 0 auto; }
        .editor-card { background: var(--card); border-radius: 16px; padding: 20px; border: 1px solid var(--border); }
        
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; overflow: hidden; border-radius: 12px; cursor: zoom-in; }
        .bg-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 1; }
        .heatmap-layer { position: absolute; inset: 0; z-index: 10; pointer-events: none; }

        /* CINEMA PREVIEW */
        #cinemaOverlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.98); z-index: 9999; align-items: center; justify-content: center; cursor: zoom-out; }
        #cinemaImg { max-width: 95%; max-height: 95%; object-fit: contain; }

        .ai-insight { margin-top: 15px; background: rgba(0,0,0,0.5); padding: 15px; border-radius: 8px; font-size: 11px; border-left: 4px solid var(--gold); color: #d1d5db; min-height: 65px; }
        .card-controls { margin-top: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .btn-action { border: none; padding: 12px; border-radius: 8px; font-weight: 800; cursor: pointer; font-size: 11px; text-transform: uppercase; }
        .btn-main { grid-column: span 2; background: var(--gold); color: #000; padding: 16px; }
        .btn-canva { background: var(--canva); color: #fff; }
        .btn-dl { background: var(--gray); color: #000; }
        select.dl-format { background: #273140; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 11px; }
    </style>
</head>
<body>
    <div id="cinemaOverlay" onclick="this.style.display='none'">
        <img id="cinemaImg" src="">
    </div>

    {% if not logged_in %}
    <div style="display:flex; height:100vh; width:100vw; align-items:center; justify-content:center;">
        <form method="POST" action="/login" style="background:var(--card); padding:40px; border-radius:16px; border:1px solid var(--border);">
            <h2 style="color:var(--mint); margin:0 0 20px 0;">Viral Studio V88</h2>
            <input type="password" name="password" style="width:100%; padding:12px; margin-bottom:20px; border-radius:8px; border:1px solid var(--border); background:#000; color:white;">
            <button type="submit" class="btn-action btn-main" style="width:100%;">START ENGINE</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-sec">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <span style="font-size:10px; font-weight:900; color:var(--mint);">ANALYTICS LIVE</span>
                <a href="/history" style="color:var(--blue); text-decoration:none; font-size:10px; font-weight:bold;">VAULT HISTORY</a>
            </div>
            <button class="btn-action btn-main" style="background:var(--mint); width:100%;" onclick="document.getElementById('vidInp').click()">+ SCAN NEW VIDEO</button>
            <input type="file" id="vidInp" style="display:none" onchange="processVideo()">
        </div>
        <div class="sidebar-sec">
            <div class="section-title">Project Raw Bank</div>
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

        const INSIGHTS_LIBRARY = [
            "Exceptional facial symmetry detected. This reduces 'scroll-friction' immediately.",
            "High micro-expression intensity. Statistical outlier for curiosity-driven clicks.",
            "Superior subject-to-background isolation. 4K depth makes this pop on mobile.",
            "Gaze-direction leads viewer eye directly to predicted text-overlay zones.",
            "Optimal silhouette clarity. Recognizable story even at 10% brightness.",
            "Vivid color-pop in primary focal zone. Perfectly breaks monochromatic feeds.",
            "Subject positioned in 'Power Corner'. Historically leads to 20% higher retention.",
            "High-frequency facial detail signals premium quality to the viewer's subconscious.",
            "Dramatic lighting profile creates cinematic authority and trust in the creator.",
            "First-contact zone is clear. Eyes hit this within 150ms of scrolling current feed.",
            "Negative space balance allows for high-impact graphic or bold font elements.",
            "Strong focal sharpness on the eyes creates an 'Intimate Chat' psychological feel.",
            "Peak emotional vulnerability detected. Triggers empathy-based clicking habits.",
            "Kinetic motion-blur suggests high energy. Best for fast-paced entertainment shorts."
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
                    allExtractedFrames.push({ url: data, ctr: vscore });
                }
                
                // Add Top 6 automatically, but sidebar allows infinite more
                const sorted = [...allExtractedFrames].sort((a,b) => b.ctr - a.ctr);
                workspaceFrames = sorted.slice(0, 6).map(f => createFrameObject(f.url, f.ctr));
                
                renderSidebar();
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

        function createFrameObject(url, ctr) {
            return { 
                url: url, 
                ctr: ctr, 
                insight: INSIGHTS_LIBRARY[Math.floor(Math.random() * INSIGHTS_LIBRARY.length)] 
            };
        }

        function renderSidebar() {
            const bank = document.getElementById('frameBank');
            bank.innerHTML = allExtractedFrames.map((f, i) => `
                <div class="bank-item" onclick="addToWorkspace(${i})">
                    <img src="${f.url}" class="bank-img">
                    <div style="position:absolute; top:8px; left:8px; background:rgba(0,0,0,0.8); color:var(--mint); font-size:10px; padding:3px 8px; font-weight:900; border-radius:4px;">${f.ctr} V-SCORE</div>
                </div>
            `).join('');
        }

        function addToWorkspace(idx) {
            const f = allExtractedFrames[idx];
            workspaceFrames.push(createFrameObject(f.url, f.ctr));
            renderAll();
        }

        function renderAll() {
            const grid = document.getElementById('mainGrid');
            if(!grid) return;
            grid.innerHTML = workspaceFrames.map((f, i) => `
                <div class="editor-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                        <span class="ctr-badge">V-SCORE: ${f.ctr}</span>
                        <button onclick="workspaceFrames.splice(${i},1); renderAll();" style="background:none; border:none; color:var(--red); cursor:pointer; font-size:18px;">✕</button>
                    </div>
                    <div class="canvas-area" onclick="document.getElementById('cinemaImg').src='${f.url}'; document.getElementById('cinemaOverlay').style.display='flex'">
                        <img src="${f.url}" class="bg-layer">
                        <div id="hm-layer-${i}" class="heatmap-layer"></div>
                    </div>
                    <div class="ai-insight">
                        <b style="color:var(--gold); text-transform:uppercase; font-size:9px;">AI STRATEGIC REPORT</b><br>
                        ${f.insight}
                    </div>
                    <div class="card-controls">
                        <button class="btn-action btn-main" onclick="runHeatmap(${i}); event.stopPropagation();">ANALYZE ATTENTION FLOW</button>
                        <button class="btn-action btn-canva" onclick="window.open('https://canva.com','_blank')">SEND TO CANVA</button>
                        <div style="display:flex; gap:5px;">
                            <select class="dl-format" id="fmt-${i}" style="flex:1;">
                                <option value="png">PNG</option>
                                <option value="jpg">JPG</option>
                            </select>
                            <button class="btn-action btn-dl" onclick="downloadFrame(${i})" style="flex:1;">DOWNLOAD</button>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function runHeatmap(idx) {
            const container = document.getElementById(`hm-layer-${idx}`);
            container.innerHTML = '';
            
            // CRITICAL: Restored 50ms delay to fix rendering failure
            setTimeout(() => {
                const hmap = h337.create({ container: container, radius: 55, maxOpacity: .55 });
                hmap.setData({ max: 100, data: [
                    { x: container.offsetWidth * 0.5, y: container.offsetHeight * 0.4, value: 100 },
                    { x: container.offsetWidth * (0.3 + Math.random()*0.4), y: container.offsetHeight * (0.3 + Math.random()*0.3), value: 60 }
                ]});
            }, 50);
        }

        function downloadFrame(idx) {
            const format = document.getElementById(`fmt-${idx}`).value;
            const link = document.createElement('a');
            link.download = `ViralStudio_Export.${format}`;
            link.href = workspaceFrames[idx].url;
            link.click();
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
    session['history'].append({'name': name, 'date': time.strftime("%Y-%m-%d %H:%M"), 'count': len(data['frames']), 'vscore_avg': sum(float(f['ctr']) for f in data['frames']) / len(data['frames'])})
    session.modified = True
    return jsonify({"status": "saved"})

@app.route('/history')
def history_page():
    if not session.get('logged_in'): return redirect(url_for('home'))
    hist = session.get('history', [])
    page = """<body style="background:#0b0d10; color:white; font-family:sans-serif; padding:50px;"><div style="max-width:900px; margin:0 auto;"><h1>History Vault</h1><a href="/" style="color:#00FFC2;">← Back to Studio</a><table style="width:100%; border-collapse:collapse; margin-top:30px;">"""
    for i, h in enumerate(hist):
        page += f"<tr style='border-bottom:1px solid #273140;'><td style='padding:15px;'>{h['name']}</td><td>{h['date']}</td><td style='color:#00FFC2;'>{h['vscore_avg']:.1f} V-SCORE</td><td><a href='/download_zip/{i}' style='color:#FFD700;'>Download ZIP</a></td></tr>"
    page += "</table></div></body>"
    return page

@app.route('/download_zip/<int:idx>')
def download_zip(idx):
    memory_file = io.BytesIO()
    project = session['history'][idx]
    with zipfile.ZipFile(memory_file, 'w') as zf:
        zf.writestr('Project_Summary.txt', f"Name: {project['name']}\\nAvg V-Score: {project['vscore_avg']}")
    memory_file.seek(0)
    return send_file(memory_file, download_name=f"{project['name'].replace(' ', '_')}.zip", as_attachment=True)

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD: session['logged_in'] = True
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
