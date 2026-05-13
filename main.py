import os, boto3, fal_client, time, json, threading, random
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "studio_ultra_secure_v52"

# 1. SECURITY CONFIGURATION
ACCESS_PASSWORD = "Heathumb2026"

# 2. BACKEND CLOUD CONFIG
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "")
jobs = {}

# 3. UNIFIED UI TEMPLATE (Login + Editor)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --pink: #FF007A; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow:hidden; }
        
        /* Login Screen */
        .login-overlay { position: fixed; inset: 0; background: var(--carbon); z-index: 10000; display: flex; align-items: center; justify-content: center; flex-direction: column; }
        .login-box { background: var(--card); padding: 40px; border-radius: 12px; border: 1px solid var(--border); text-align: center; width: 320px; }
        .login-input { width: 100%; padding: 12px; margin: 20px 0; background: #000; border: 1px solid var(--border); color: var(--mint); text-align: center; font-size: 18px; border-radius: 4px; }
        
        /* Main Layout */
        .sidebar { width: 350px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; display: flex; flex-direction: column; }
        .sidebar-sec { padding: 15px; border-bottom: 1px solid var(--border); }
        .section-title { font-size: 10px; font-weight: 900; color: var(--blue); text-transform: uppercase; margin-bottom: 12px; }
        .workspace { flex: 1; padding: 25px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; max-width: 1400px; margin: 0 auto; }

        /* Layers & Effects */
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; overflow: hidden; border-radius: 6px; border: 5px solid transparent; }
        .bg-layer { position: absolute; width: 100%; height: 100%; object-fit: cover; z-index: 1; transition: filter 0.3s; }
        .subject-layer { position: absolute; width: 100%; height: 100%; object-fit: cover; z-index: 2; pointer-events: none; }
        .sticker-mode { filter: drop-shadow(0 0 12px rgba(255,255,255,0.9)) drop-shadow(0 0 2px #fff); }

        /* Draggables */
        .drag-item { position: absolute; cursor: move; z-index: 10; user-select: none; }
        .overlay-text { font-weight: 900; text-transform: uppercase; white-space: nowrap; padding: 5px; color: #fff; text-shadow: 2px 2px 4px #000; }

        .c-btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 8px; font-size: 10px; cursor: pointer; border-radius: 4px; font-weight: 700; width: 100%; margin-top: 5px; }
        .c-btn:hover { border-color: var(--mint); }

        /* Preview Modal */
        #previewModal { position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 9999; display: none; align-items: center; justify-content: center; }
        #previewImg { max-width: 90%; max-height: 90%; border: 4px solid var(--mint); }

        .frame-bank { padding: 15px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .bank-item { border-radius: 4px; overflow: hidden; border: 1px solid #333; cursor: pointer; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div class="login-overlay">
        <div class="login-box">
            <div class="section-title" style="color:var(--mint)">Viral Studio V52</div>
            <form method="POST" action="/login">
                <input type="password" name="password" class="login-input" placeholder="ENTER CODE" autofocus>
                <button type="submit" class="c-btn" style="background:var(--mint); color:#000; padding:12px;">AUTHORIZE ACCESS</button>
            </form>
        </div>
    </div>
    {% else %}
    <div id="previewModal" onclick="this.style.display='none'"><img id="previewImg" src=""></div>

    <div class="sidebar">
        <div class="sidebar-sec">
            <button class="c-btn" style="background:var(--mint); color:#000;" onclick="document.getElementById('vidInp').click()">+ SELECT VIDEO SOURCE</button>
            <input type="file" id="vidInp" style="display:none" onchange="uploadVideo()">
            <button class="c-btn" style="margin-top:10px; background:var(--pink);" onclick="location.href='/logout'">LOGOUT</button>
        </div>

        <div class="sidebar-sec">
            <div class="section-title">Smart Effects</div>
            <label style="font-size:10px;">Depth of Field (Blur)</label>
            <input type="range" min="0" max="25" value="0" style="width:100%" oninput="applyBlur(this.value)">
            <button class="c-btn" onclick="toggleSticker()">✨ TOGGLE WHITE GLOW</button>
        </div>

        <div class="sidebar-sec">
            <div class="section-title">Branding & Style</div>
            <input type="color" id="colorInp" style="width:100%; height:30px;" onchange="updateColor(this.value)">
            <button class="c-btn" onclick="document.getElementById('logoInp').click()">UPLOAD LOGOS</button>
            <input type="file" id="logoInp" style="display:none" multiple onchange="loadLogos()">
            <div id="logoBank" style="display:grid; grid-template-columns:repeat(3,1fr); gap:5px; margin-top:10px;"></div>
        </div>

        <div class="section-title" style="padding:15px 15px 0 15px;">Frame Bank</div>
        <div class="frame-bank" id="frameBank"></div>
    </div>

    <div class="workspace">
        <div id="status" style="text-align:center; margin-bottom:20px; font-weight:900; color:var(--blue);">Ready for Content</div>
        <div id="mainGrid" class="main-grid"></div>
    </div>
    {% endif %}

    <script>
        let allFrames = [];
        let workspaceFrames = [];
        let blurVal = 0;
        let isSticker = false;
        let activeColor = "#FFFFFF";

        function uploadVideo() {
            const fd = new FormData();
            fd.append('video', document.getElementById('vidInp').files[0]);
            document.getElementById('status').innerText = "AI Extracting 6 Diverse Keyframes...";
            fetch('/process', { method: 'POST', body: fd }).then(r => r.json()).then(data => pollStatus(data.job_id));
        }

        function pollStatus(jid) {
            fetch(`/status/${jid}`).then(r => r.json()).then(data => {
                if (data.status === 'completed') {
                    allFrames = data.frames;
                    workspaceFrames = data.chosen_indices.map(idx => allFrames[idx]);
                    renderAll();
                } else { setTimeout(() => pollStatus(jid), 3000); }
            });
        }

        function renderAll() {
            document.getElementById('frameBank').innerHTML = allFrames.map((u, i) => `
                <div class="bank-item" onclick="swapToWorkspace(${i})"><img src="${u}" style="width:100%;"></div>
            `).join('');

            document.getElementById('mainGrid').innerHTML = workspaceFrames.map((u, i) => `
                <div class="editor-card">
                    <div class="canvas-area" id="export-${i}">
                        <img src="${u}" class="bg-layer" style="filter:blur(${blurVal}px)">
                        <img src="${u}" class="subject-layer ${isSticker ? 'sticker-mode' : ''}">
                        <div class="drag-item overlay-text" contenteditable="true" style="color:${activeColor}">NEW VIRAL HIT</div>
                    </div>
                    <div class="controls">
                        <button class="c-btn" onclick="fullPreview(${i})">👁️ PREVIEW</button>
                        <button class="c-btn" onclick="downloadFrame(${i})">💾 DOWNLOAD</button>
                    </div>
                </div>
            `).join('');
            setupDraggables();
        }

        function fullPreview(i) {
            html2canvas(document.getElementById(`export-${i}`), { useCORS: true, scale: 2 }).then(canvas => {
                document.getElementById('previewImg').src = canvas.toDataURL();
                document.getElementById('previewModal').style.display = 'flex';
            });
        }

        function downloadFrame(i) {
            html2canvas(document.getElementById(`export-${i}`), { useCORS: true }).then(canvas => {
                const link = document.createElement('a');
                link.download = `Viral_Studio_V52_${i}.png`;
                link.href = canvas.toDataURL();
                link.click();
            });
        }

        function setupDraggables() {
            document.querySelectorAll('.drag-item').forEach(el => {
                el.onmousedown = function(e) {
                    let ox = e.clientX - el.offsetLeft;
                    let oy = e.clientY - el.offsetTop;
                    document.onmousemove = function(e) {
                        el.style.left = (e.clientX - ox) + 'px';
                        el.style.top = (e.clientY - oy) + 'px';
                    }
                    document.onmouseup = () => document.onmousemove = null;
                }
            });
        }

        function applyBlur(v) { blurVal = v; renderAll(); }
        function toggleSticker() { isSticker = !isSticker; renderAll(); }
        function updateColor(v) { activeColor = v; renderAll(); }
        function swapToWorkspace(allIdx, wsIdx = 0) { workspaceFrames[wsIdx] = allFrames[allIdx]; renderAll(); }
        function loadLogos() { /* Multi-logo sidebar logic as per V51 */ }
    </script>
</body>
</html>
"""

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD:
        session['logged_in'] = True
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/process', methods=['POST'])
def process():
    if not session.get('logged_in'): return jsonify({"status": "unauthorized"})
    video = request.files['video']
    job_id = str(int(time.time()))
    temp_fn = f"raw_{job_id}.mp4"
    s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read', 'ContentType': 'video/mp4'})
    v_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{temp_fn}"
    
    # SMART SAMPLING: Pick 6 frames from start, middle, and end
    handler = fal_client.submit("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
    chosen = [random.randint(0,4), random.randint(5,9), random.randint(10,14), 
              random.randint(15,19), random.randint(20,24), random.randint(25,29)]
    
    jobs[job_id] = {'status': 'processing', 'indices': chosen}
    threading.Thread(target=background_monitor, args=(job_id, handler, temp_fn)).start()
    return jsonify({"job_id": job_id})

def background_monitor(jid, handler, s3_key):
    try:
        result = handler.get()
        frames = [i['url'] for i in result.get('images', [])]
        s3.delete_object(Bucket=BUCKET, Key=s3_key) # PURGE S3 VIDEO IMMEDIATELY
        jobs[jid]['status'] = 'completed'
        jobs[jid]['frames'] = frames
    except: jobs[jid]['status'] = 'error'

@app.route('/status/<job_id>')
def status(job_id):
    job = jobs.get(job_id, {'status': 'not_found'})
    return jsonify({'status': job['status'], 'frames': job.get('frames', []), 'chosen_indices': job.get('indices', [])})

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
