import os, boto3, fal_client, time, json, threading
from flask import Flask, request, jsonify, render_template_string, session, redirect

app = Flask(__name__)
app.secret_key = "studio_secret_key"
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 
ACCESS_PASSWORD = "CREATOR_PRO_2026"

os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "")
PROJECTS_FILE = "user_vault.json"

jobs = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; }
        
        /* Sidebar (The Frame Bank) */
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .bank-header { padding: 20px; font-weight: 900; color: var(--blue); border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
        .frame-bank { flex: 1; overflow-y: auto; padding: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .bank-item { position: relative; border-radius: 4px; overflow: hidden; border: 1px solid #333; }
        .bank-img { width: 100%; aspect-ratio: 16/9; object-fit: cover; cursor: zoom-in; }
        .add-btn { position: absolute; top: 5px; right: 5px; background: var(--mint); color: #000; border: none; border-radius: 50%; width: 24px; height: 24px; font-weight: 900; cursor: pointer; }

        /* Workspace Grid */
        .workspace { flex: 1; padding: 20px; background: #080a0d; overflow-y: auto; display: flex; flex-direction: column; align-items: center; }
        .upload-row { display: flex; gap: 20px; align-items: center; margin-bottom: 20px; }
        .main-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; width: 100%; max-width: 1200px; }
        
        /* Individual Editor Card */
        .editor-card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; padding: 10px; }
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; overflow: hidden; }
        .canvas-img { width: 100%; height: 100%; object-fit: cover; }
        
        .overlay-text { 
            position: absolute; top: 20%; left: 10%; color: white; font-weight: 900; text-transform: uppercase; 
            text-shadow: 2px 2px 0 #000; cursor: move; font-size: 20px; line-height: 1; pointer-events: auto;
        }

        /* Per-Picture Controls */
        .controls { margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        .control-input { background: #000; border: 1px solid #333; color: #fff; padding: 5px; border-radius: 4px; font-size: 11px; grid-column: span 2; }
        .c-btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 5px; font-size: 10px; cursor: pointer; border-radius: 3px; font-weight: 700; }
        .c-btn:hover { border-color: var(--mint); color: var(--mint); }
        .color-row { display: flex; gap: 5px; grid-column: span 2; align-items: center; font-size: 10px; }

        /* Preview Modal */
        #previewModal { position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 1000; display: none; align-items: center; justify-content: center; cursor: zoom-out; }
        #previewImg { max-width: 90%; max-height: 90%; border: 3px solid var(--mint); }
    </style>
</head>
<body>
    <div id="previewModal" onclick="this.style.display='none'"><img id="previewImg" src=""></div>

    <div class="sidebar">
        <div class="bank-header">Frame Bank (30 Extracted)</div>
        <div id="frameBank" class="frame-bank"></div>
    </div>

    <div class="workspace">
        <div class="upload-row">
            <input type="file" id="vidInp" style="display:none;" onchange="upload()">
            <button style="background:var(--mint); padding:10px 25px; border-radius:50px; font-weight:900; border:none; cursor:pointer;" onclick="document.getElementById('vidInp').click()">+ NEW PROJECT</button>
            <div id="status" style="color:var(--blue); font-size:12px; font-weight:700;">Ready.</div>
        </div>

        <div id="mainGrid" class="main-grid">
            <!-- 6 Editor Cards Generated Here -->
        </div>
    </div>

    <script>
        let allFrames = [];
        let workspaceFrames = [];

        function upload() {
            const fd = new FormData();
            fd.append('video', document.getElementById('vidInp').files[0]);
            document.getElementById('status').innerText = "Uploading & Purging Video...";
            fetch('/process', { method: 'POST', body: fd }).then(r => r.json()).then(data => pollStatus(data.job_id));
        }

        function pollStatus(jid) {
            fetch(`/status/${jid}`).then(r => r.json()).then(data => {
                if (data.status === 'completed') {
                    allFrames = data.frames;
                    workspaceFrames = allFrames.slice(0, 6);
                    renderAll();
                } else { setTimeout(() => pollStatus(jid), 3000); }
            });
        }

        function renderAll() {
            // Render Bank
            document.getElementById('frameBank').innerHTML = allFrames.map((u, i) => `
                <div class="bank-item">
                    <img src="${u}" class="bank-img" onclick="preview('${u}')">
                    <button class="add-btn" onclick="addToWorkspace(${i})">+</button>
                </div>
            `).join('');

            // Render Workspace (6 Pictures)
            document.getElementById('mainGrid').innerHTML = workspaceFrames.map((u, i) => `
                <div class="editor-card" id="card-${i}">
                    <div class="canvas-area">
                        <img src="${u}" class="canvas-img" onclick="preview('${u}')">
                        <div class="overlay-text" id="text-${i}" contenteditable="true">EDIT ME</div>
                    </div>
                    <div class="controls">
                        <input type="text" class="control-input" placeholder="Text..." oninput="updateText(${i}, this.value)">
                        <button class="c-btn" onclick="adjSize(${i}, 5)">Size +</button>
                        <button class="c-btn" onclick="adjSize(${i}, -5)">Size -</button>
                        <button class="c-btn" onclick="toggleBorder(${i})">Border</button>
                        <button class="c-btn" onclick="alert('Logo Added')">Add Logo</button>
                        <div class="color-row">
                            Color: <input type="color" onchange="updateColor(${i}, this.value)" style="height:20px; width:100%;">
                        </div>
                        <button class="c-btn" style="grid-column:span 2; background:var(--blue); color:#000;" onclick="window.print()">Download PNG</button>
                    </div>
                </div>
            `).join('');
            setupDraggable();
        }

        function addToWorkspace(idx) {
            workspaceFrames.shift(); // Remove oldest
            workspaceFrames.push(allFrames[idx]);
            renderAll();
        }

        function preview(url) {
            document.getElementById('previewImg').src = url;
            document.getElementById('previewModal').style.display = 'flex';
        }

        function updateText(i, val) { document.getElementById(`text-${i}`).innerText = val; }
        function adjSize(i, val) { 
            let el = document.getElementById(`text-${i}`);
            let cur = parseInt(window.getComputedStyle(el).fontSize);
            el.style.fontSize = (cur + val) + 'px';
        }
        function updateColor(i, val) { document.getElementById(`text-${i}`).style.color = val; }
        function toggleBorder(i) {
            let el = document.getElementById(`text-${i}`);
            el.style.webkitTextStroke = el.style.webkitTextStroke ? "" : "1px black";
        }

        function setupDraggable() {
            document.querySelectorAll('.overlay-text').forEach(el => {
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
        
        function renderEmpty() {
            document.getElementById('mainGrid').innerHTML = Array(6).fill('<div class="editor-card" style="height:200px; display:flex; align-items:center; justify-content:center; color:#333;">Empty Slot</div>').join('');
        }
        renderEmpty();
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC (Same as V44 for stability) ---
@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD: session['logged_in'] = True
    return redirect('/')

@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    job_id = str(int(time.time())); jobs[job_id] = {'status': 'processing'}
    temp_fn = f"raw_{job_id}.mp4"
    s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read', 'ContentType': 'video/mp4'})
    v_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{temp_fn}"
    handler = fal_client.submit("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
    threading.Thread(target=background_monitor, args=(job_id, handler, temp_fn)).start()
    return jsonify({"job_id": job_id})

def background_monitor(jid, handler, s3_key):
    try:
        result = handler.get()
        frames = [i['url'] for i in result.get('images', [])]
        s3.delete_object(Bucket=BUCKET, Key=s3_key) # PURGE
        jobs[jid] = {'status': 'completed', 'frames': frames}
    except: jobs[jid] = {'status': 'error'}

@app.route('/status/<job_id>')
def status(job_id): return jsonify(jobs.get(job_id, {'status': 'not_found'}))

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
