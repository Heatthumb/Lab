import os, boto3, fal_client, time, json
from flask import Flask, request, jsonify, render_template_string, session, redirect

app = Flask(__name__)
app.secret_key = "studio_secret_key"
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 

# --- CONFIG ---
ACCESS_PASSWORD = "CREATOR_PRO_2026"
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "")
PROJECTS_FILE = "user_vault.json"

# Global dictionary to track background jobs
jobs = {}

def get_next_id():
    if not os.path.exists(PROJECTS_FILE): return "101"
    with open(PROJECTS_FILE, "r") as f:
        try:
            data = json.load(f)
            nums = [int(k) for k in data.keys() if k.isdigit()]
            return str(max(nums) + 1) if nums else "101"
        except: return "101"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 280px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; }
        .sidebar-header { padding: 20px; font-weight: 900; color: var(--blue); border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
        .proj-item { padding: 15px; border-bottom: 1px solid #1e252e; cursor: pointer; font-size: 12px; color: #8a99af; transition: 0.2s; }
        .proj-item:hover { background: #1c232d; color: var(--mint); }
        .workspace { flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; background: #080a0d; overflow-y: auto; }
        .upload-btn { background: var(--mint); color: #000; padding: 12px 30px; border-radius: 50px; font-weight: 900; cursor: pointer; border: none; margin-bottom: 15px; }
        .status-box { font-size: 12px; color: var(--blue); font-weight: 700; margin-bottom: 15px; }
        .frames-strip { width: 950px; display: flex; gap: 10px; padding: 15px 0; overflow-x: auto; border-bottom: 1px solid var(--border); margin-bottom: 15px; min-height: 100px; }
        .thumb { width: 130px; height: 75px; object-fit: cover; border-radius: 6px; cursor: pointer; border: 2px solid transparent; }
        .canvas-wrap { position: relative; width: 854px; height: 480px; background: #000; border-radius: 12px; overflow: hidden; border: 3px solid var(--border); }
        #bgImg { width: 100%; height: 100%; object-fit: cover; }
        .draggable { position: absolute; cursor: move; user-select: none; font-weight: 900; color: white; text-transform: uppercase; text-shadow: 2px 2px 0 #000; font-size: 50px; z-index: 5; }
        .toolbar { width: 854px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; background: var(--card); padding: 15px; margin-top: 10px; border-radius: 12px; border: 1px solid var(--border); }
        .btn { width: 100%; padding: 10px; background: #242b35; border: 1px solid var(--border); color: #fff; border-radius: 6px; cursor: pointer; font-weight: 700; font-size: 11px; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div style="display:flex; align-items:center; justify-content:center; width:100%;">
        <form method="POST" action="/login" style="background:var(--card); padding:30px; border-radius:12px; text-align:center; border:1px solid var(--border);">
            <h3 style="color:var(--blue)">STUDIO ACCESS</h3>
            <input type="password" name="password" style="padding:10px; background:#000; border:1px solid #333; color:#fff;" placeholder="Code" required><br><br>
            <button type="submit" class="btn" style="background:var(--mint); color:#000">ENTER</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-header">HISTORY ARCHIVE</div>
        <div id="projectList"></div>
    </div>
    <div class="workspace">
        <input type="file" id="vidInp" style="display:none;" onchange="upload()">
        <button class="upload-btn" id="upBtn" onclick="document.getElementById('vidInp').click()">+ LOAD VIDEO</button>
        <div id="status" class="status-box">Ready for next project.</div>
        <div id="framesStrip" class="frames-strip"></div>
        <div class="canvas-wrap">
            <img id="bgImg" src="">
            <div id="textLayer" class="draggable">EDIT ME</div>
        </div>
        <div class="toolbar">
            <div><input type="text" id="textInp" oninput="updateText()" style="width:90%; padding:8px; background:#000; color:#fff; border:1px solid #333;"></div>
            <div><button class="btn" onclick="zoom(1.8)">EMOTION ZOOM</button></div>
            <div><button class="btn" onclick="window.print()">SAVE HQ PNG</button></div>
        </div>
    </div>
    {% endif %}

    <script>
        let currentJob = null;

        function upload() {
            const file = document.getElementById('vidInp').files[0];
            const fd = new FormData();
            fd.append('video', file);
            
            document.getElementById('status').innerText = "Uploading to Cloud...";
            document.getElementById('upBtn').disabled = true;

            fetch('/process', { method: 'POST', body: fd })
                .then(r => r.json())
                .then(data => {
                    currentJob = data.job_id;
                    checkStatus();
                });
        }

        function checkStatus() {
            if (!currentJob) return;
            document.getElementById('status').innerText = "AI Extracting 30 Frames (Streaming)...";
            
            fetch(`/status/${currentJob}`)
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'completed') {
                        document.getElementById('status').innerText = "Process Complete. Video Purged.";
                        renderFrames(data.frames);
                        loadVault();
                        document.getElementById('upBtn').disabled = false;
                        currentJob = null;
                    } else if (data.status === 'error') {
                        document.getElementById('status').innerText = "Error: Extraction Failed.";
                        document.getElementById('upBtn').disabled = false;
                    } else {
                        setTimeout(checkStatus, 2000); // Check again in 2 seconds
                    }
                });
        }

        function renderFrames(frames) {
            document.getElementById('framesStrip').innerHTML = frames.map(u => `<img src="${u}" class="thumb" onclick="setCanvas('${u}')">`).join('');
            if(frames.length > 0) setCanvas(frames[0]);
        }
        function setCanvas(url) { document.getElementById('bgImg').src = url; }
        async function loadVault() {
            const res = await fetch('/get_vault');
            const data = await res.json();
            document.getElementById('projectList').innerHTML = Object.keys(data).sort((a,b)=>b-a).map(n => `<div class="proj-item" onclick="openProj('${n}')">📁 Project #${n}</div>`).join('');
        }
        async function openProj(n) {
            const res = await fetch('/get_vault');
            const data = await res.json();
            renderFrames(data[n]);
        }
        function updateText() { document.getElementById('textLayer').innerText = document.getElementById('textInp').value; }
        function zoom(s) { document.getElementById('bgImg').style.transform = `scale(${s})`; }
        {% if logged_in %} loadVault(); {% endif %}
    </script>
</body>
</html>
"""

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD: session['logged_in'] = True
    return redirect('/')

@app.route('/process', methods=['POST'])
def process():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    video = request.files['video']
    job_id = str(int(time.time()))
    jobs[job_id] = {'status': 'processing'}
    
    # Run upload and trigger AI
    temp_fn = f"raw_{job_id}.mp4"
    s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read'})
    v_url = f"https://{BUCKET}.s3.amazonaws.com/{temp_fn}"

    # Use SUBMIT (Non-blocking) instead of SUBSCRIBE (Blocking)
    handler = fal_client.submit("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
    
    def background_work(jid, h, s3_key):
        try:
            result = h.get() # Wait for AI in background
            frames = [i['url'] for i in result.get('images', [])]
            s3.delete_object(Bucket=BUCKET, Key=s3_key) # Immediate Purge
            p_id = get_next_id()
            with open(PROJECTS_FILE, "r+") as f:
                v = json.load(f); v[p_id] = frames
                f.seek(0); json.dump(v, f); f.truncate()
            jobs[jid] = {'status': 'completed', 'frames': frames}
        except: jobs[jid] = {'status': 'error'}

    import threading
    threading.Thread(target=background_work, args=(job_id, handler, temp_fn)).start()
    return jsonify({"job_id": job_id})

@app.route('/status/<job_id>')
def status(job_id):
    return jsonify(jobs.get(job_id, {'status': 'not_found'}))

@app.route('/get_vault')
def get_vault():
    if not os.path.exists(PROJECTS_FILE): return jsonify({})
    with open(PROJECTS_FILE, "r") as f: return jsonify(json.load(f))

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
