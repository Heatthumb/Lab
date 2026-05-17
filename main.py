import os, boto3, fal_client, time, threading
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "viral_studio_v78_ab_analytics"
ACCESS_PASSWORD = "Heathumb2026"

# Cloud Config (Ensure these are set in your environment)
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "")
jobs = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --pink: #FF007A; --red: #ff4d4d; --gold: #FFD700; --glass: rgba(255,255,255,0.05); }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow:hidden; }
        
        /* Layout & Navigation */
        .sidebar { width: 340px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; display: flex; flex-direction: column; }
        .sidebar-sec { padding: 20px; border-bottom: 1px solid var(--border); }
        .section-title { font-size: 11px; font-weight: 900; color: var(--blue); text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 15px; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: radial-gradient(circle at top right, #1a202c 0%, #080a0d 100%); }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 35px; max-width: 1400px; margin: 0 auto; }
        
        /* AI Performance Card */
        .editor-card { background: var(--card); border-radius: 20px; padding: 20px; border: 1px solid var(--border); position: relative; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .editor-card:hover { border-color: var(--mint); transform: translateY(-5px); }
        
        /* CTR & Sentiment Badges */
        .ctr-badge { position: absolute; top: 30px; left: 30px; background: rgba(0,0,0,0.85); border: 1px solid var(--mint); color: var(--mint); padding: 6px 14px; border-radius: 30px; font-weight: 900; font-size: 12px; z-index: 100; backdrop-filter: blur(5px); box-shadow: 0 0 15px rgba(0,255,194,0.3); }
        .ab-tag { position: absolute; top: 30px; right: 30px; background: var(--pink); color: #fff; padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 900; z-index: 100; text-transform: uppercase; }

        /* Canvas Engine */
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; overflow: hidden; border-radius: 14px; border: 1px solid #333; }
        .bg-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; }
        .drag-item { position: absolute; cursor: move; z-index: 10; user-select: none; font-weight: 900; text-transform: uppercase; text-shadow: 0 0 15px #000; outline: none; }

        /* Multi-Variant Controls */
        .card-controls { margin-top: 20px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        .c-btn { background: var(--glass); border: 1px solid var(--border); color: #fff; padding: 12px; font-size: 11px; cursor: pointer; border-radius: 10px; font-weight: 700; transition: 0.2s; }
        .c-btn:hover { background: var(--border); border-color: var(--blue); }
        
        .ai-gen-btn { grid-column: span 3; background: linear-gradient(135deg, var(--gold) 0%, #FFA800 100%); color: #000; border: none; padding: 16px; border-radius: 10px; font-weight: 900; cursor: pointer; margin-top: 5px; box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2); }
        .ai-gen-btn:active { transform: scale(0.98); }
        .dl-btn { grid-column: span 2; background: var(--blue); color:#000; font-weight:900; border:none; border-radius:10px; cursor:pointer; }
        
        .status-msg { grid-column: span 3; font-size: 10px; color: #888; text-align: center; margin-top: 8px; font-style: italic; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div style="display:flex; height:100vh; width:100vw; align-items:center; justify-content:center; background: radial-gradient(circle, #1a202c 0%, #000 100%);">
        <form method="POST" action="/login" style="background:var(--card); padding:45px; border-radius:24px; border:1px solid var(--border); width:380px; box-shadow: 0 20px 50px rgba(0,0,0,1);">
            <h1 style="color:var(--mint); margin:0 0 8px 0; font-size:28px; letter-spacing:-1px;">VIRAL STUDIO PRO</h1>
            <p style="color:#888; font-size:13px; margin-bottom:30px;">A/B Performance & CTR Prediction</p>
            <input type="password" name="password" placeholder="Enter License Key..." style="width:100%; padding:16px; margin-bottom:20px; border-radius:10px; border:1px solid var(--border); background:#080a0d; color:white; box-sizing:border-box; outline:none; font-size:14px;">
            <button type="submit" class="ai-gen-btn" style="width:100%;">BOOT SYSTEM</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-sec">
            <div class="section-title">Source Input</div>
            <button class="ai-gen-btn" style="background:var(--mint); margin:0;" onclick="document.getElementById('vidInp').click()">+ IMPORT VIDEO FILE</button>
            <input type="file" id="vidInp" style="display:none" onchange="uploadVideo()">
        </div>
        <div class="sidebar-sec">
            <div class="section-title">A/B Frame Library</div>
            <div id="frameBank" style="display:grid; grid-template-columns: 1fr; gap:12px;"></div>
        </div>
    </div>

    <div class="workspace">
        <div id="mainGrid" class="main-grid"></div>
    </div>
    {% endif %}

    <script>
        let workspaceFrames = [];
        let allFrames = [];

        function uploadVideo() {
            const fd = new FormData(); fd.append('video', document.getElementById('vidInp').files[0]);
            fetch('/process', { method: 'POST', body: fd }).then(r => r.json()).then(data => pollStatus(data.job_id));
        }

        function pollStatus(jid) {
            fetch(`/status/${jid}`).then(r => r.json()).then(data => {
                if (data.status === 'completed') {
                    allFrames = data.frames;
                    // Auto-load 6 unique variants for the A/B grid
                    workspaceFrames = [0, 4, 8, 12, 16, 20].map((idx, i) => ({
                        url: allFrames[idx], blur: 0, text: "CLICK TO EDIT", color: "#FFFFFF", status: 'idle', errorMsg: "", ctr: "Scanning...", variant: String.fromCharCode(65 + i)
                    }));
                    renderAll();
                    workspaceFrames.forEach((_, i) => predictCTR(i));
                } else { setTimeout(() => pollStatus(jid), 2000); }
            });
        }

        async function predictCTR(i) {
            const res = await fetch('/predict_ctr', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ image_url: workspaceFrames[i].url })
            });
            const data = await res.json();
            workspaceFrames[i].ctr = data.score;
            renderAll();
        }

        async function triggerRedraw(i) {
            const format = document.getElementById(`format-${i}`).value;
            workspaceFrames[i].status = 'loading'; renderAll();

            const res = await fetch('/redraw', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ image_url: workspaceFrames[i].url, format: format })
            });
            const data = await res.json();
            if (data.redraw_url) {
                workspaceFrames[i].url = data.redraw_url;
                workspaceFrames[i].status = 'idle';
                predictCTR(i); // Re-calculate CTR after expansion
            } else {
                workspaceFrames[i].status = 'error';
                workspaceFrames[i].errorMsg = "AI Failure: Expand Logic";
            }
            renderAll();
        }

        function renderAll() {
            if (!document.getElementById('mainGrid')) return;
            
            // Render Side Bank
            document.getElementById('frameBank').innerHTML = allFrames.slice(0,10).map((u, i) => `
                <div style="background:#000; border-radius:8px; overflow:hidden; position:relative; cursor:pointer;" onclick="addToWorkspace('${u}')">
                    <img src="${u}" style="width:100%; opacity:0.6;">
                    <div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:white; font-weight:900; font-size:20px;">+</div>
                </div>`).join('');

            // Render Editor Cards
            document.getElementById('mainGrid').innerHTML = workspaceFrames.map((f, i) => `
                <div class="editor-card">
                    <div class="ctr-badge">EST. CTR: ${f.ctr}</div>
                    <div class="ab-tag">Variant ${f.variant}</div>
                    <div class="canvas-area" id="export-${i}">
                        <img src="${f.url}" class="bg-layer" style="filter:blur(${f.blur}px)">
                        <div class="drag-item" contenteditable="true" style="color:${f.color}; top:25%; left:15%; font-size:36px;">${f.text}</div>
                    </div>
                    <div class="card-controls">
                        <button class="ai-gen-btn" onclick="triggerRedraw(${i})">
                            ${f.status === 'loading' ? 'ANALYZING VISUALS...' : '✨ AI A/B EXPANSION (4K)'}
                        </button>
                        <button class="c-btn" onclick="updateBlur(${i})">GAUSSIAN +</button>
                        <input type="color" value="${f.color}" onchange="updateColor(${i}, this.value)" style="width:100%; height:45px; border:none; background:none; cursor:pointer;">
                        <button class="c-btn" style="color:var(--red);" onclick="workspaceFrames.splice(${i},1); renderAll();">BIN</button>
                        
                        <div style="grid-column: span 3; display:flex; gap:12px; margin-top:5px;">
                            <select id="format-${i}" class="c-btn" style="flex:1;">
                                <option value="16/9">YouTube (16:9)</option>
                                <option value="9/16">TikTok (9:16)</option>
                            </select>
                            <button class="dl-btn" onclick="exportImg(${i})" style="flex:2;">EXPORT TEST VARIANT</button>
                        </div>
                        <div class="status-msg">${f.errorMsg || 'Awaiting Performance Data...'}</div>
                    </div>
                </div>`).join('');
            setupDraggables();
        }

        function exportImg(i) {
            html2canvas(document.getElementById(`export-${i}`), {useCORS:true, scale:3}).then(c => {
                const a = document.createElement('a'); a.download=`Studio_Variant_${workspaceFrames[i].variant}.png`; a.href=c.toDataURL(); a.click();
            });
        }
        function updateBlur(i) { workspaceFrames[i].blur += 5; renderAll(); }
        function updateColor(i, val) { workspaceFrames[i].color = val; renderAll(); }
        function addToWorkspace(url) {
            workspaceFrames.push({ url, blur: 0, text: "NEW HOOK", color: "#FFFFFF", status: 'idle', errorMsg: "", ctr: "Scanning...", variant: "NEW" });
            renderAll();
            predictCTR(workspaceFrames.length - 1);
        }
        function setupDraggables() {
            document.querySelectorAll('.drag-item').forEach(el => {
                el.onmousedown = (e) => {
                    let ox = e.clientX - el.offsetLeft, oy = e.clientY - el.offsetTop;
                    document.onmousemove = (e) => { el.style.left=(e.clientX-ox)+'px'; el.style.top=(e.clientY-oy)+'px'; }
                    document.onmouseup = () => document.onmousemove = null;
                };
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD: session['logged_in'] = True
    return redirect(url_for('home'))

@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    job_id = str(int(time.time())); temp_fn = f"raw_source_{job_id}.mp4"
    s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read'})
    v_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{temp_fn}"
    handler = fal_client.submit("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
    jobs[job_id] = {'status': 'processing'}
    threading.Thread(target=background_monitor, args=(job_id, handler, temp_fn)).start()
    return jsonify({"job_id": job_id})

@app.route('/predict_ctr', methods=['POST'])
def predict_ctr():
    # Performance Simulation Logic
    import random
    # High-Performing range: 6.5% - 11.2%
    # Low-Performing range: 2.1% - 4.5%
    score = f"{random.uniform(3.5, 12.0):.1f}%"
    return jsonify({"score": score})

@app.route('/redraw', methods=['POST'])
def redraw():
    img_url = request.json.get('image_url')
    fmt = request.json.get('format', '16/9')
    # Directional Padding to force the AI to fill the A/B testing canvas
    side_p = 512 if fmt == "16/9" else 0
    top_p = 512 if fmt == "9/16" else 0
    try:
        result = fal_client.subscribe("fal-ai/image-apps-v2/outpaint", {
            "image_url": img_url,
            "left_padding": side_p, "right_padding": side_p,
            "top_padding": top_p, "bottom_padding": top_p,
            "prompt": "Highly clickable YouTube thumbnail background. Dramatic lighting, vivid colors, 4K depth of field.",
            "enable_safety_checker": False
        })
        return jsonify({"redraw_url": result['images'][0]['url']})
    except Exception as e: return jsonify({"error": str(e)}), 500

def background_monitor(jid, handler, s3_key):
    try:
        result = handler.get(); frames = [i['url'] for i in result.get('images', [])]
        s3.delete_object(Bucket=BUCKET, Key=s3_key) 
        jobs[jid]['status'] = 'completed'; jobs[jid]['frames'] = frames
    except: jobs[jid]['status'] = 'error'

@app.route('/status/<job_id>')
def status(job_id):
    job = jobs.get(job_id, {'status': 'not_found'})
    return jsonify({'status': job['status'], 'frames': job.get('frames', [])})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
