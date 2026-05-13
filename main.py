import os, boto3, fal_client, time, json, threading
from flask import Flask, request, jsonify, render_template_string, session, redirect

app = Flask(__name__)
app.secret_key = "studio_secret_key"

# --- CONFIGURATION ---
# Allows up to 500MB video uploads to prevent server crashes
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 
ACCESS_PASSWORD = "CREATOR_PRO_2026"

# Environment Variables
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "")
PROJECTS_FILE = "user_vault.json"

# In-memory job tracker for the UI
jobs = {}

def get_next_id():
    """Calculates the next project ID starting from 101."""
    if not os.path.exists(PROJECTS_FILE): return "101"
    with open(PROJECTS_FILE, "r") as f:
        try:
            data = json.load(f)
            nums = [int(k) for k in data.keys() if k.isdigit()]
            return str(max(nums + [100]) + 1)
        except: return "101"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Viral Studio V43</title>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar (Full History) */
        .sidebar { width: 280px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; }
        .sidebar-header { padding: 25px; font-weight: 900; color: var(--blue); border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
        .proj-item { padding: 15px 25px; border-bottom: 1px solid #1e252e; cursor: pointer; font-size: 13px; transition: 0.2s; color: #8a99af; }
        .proj-item:hover { background: #1c232d; color: var(--mint); }

        /* Workspace */
        .workspace { flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; background: #080a0d; overflow-y: auto; }
        .upload-btn { background: var(--mint); color: #000; padding: 14px 30px; border-radius: 50px; font-weight: 900; cursor: pointer; border: none; margin-bottom: 10px; }
        .upload-btn:disabled { background: #333; color: #777; cursor: not-allowed; }
        
        .status-box { font-size: 12px; color: var(--blue); font-weight: 700; margin-bottom: 15px; min-height: 15px; }

        /* Frames Strip */
        .frames-strip { width: 950px; display: flex; gap: 12px; padding: 20px 0; overflow-x: auto; border-bottom: 1px solid var(--border); margin-bottom: 20px; min-height: 110px; }
        .thumb { width: 140px; height: 80px; object-fit: cover; border-radius: 6px; cursor: pointer; border: 2px solid transparent; transition: 0.2s; }
        .thumb:hover { transform: scale(1.3); z-index: 10; border-color: var(--mint); box-shadow: 0 10px 30px #000; }

        /* Canvas Workspace */
        .canvas-wrap { position: relative; width: 854px; height: 480px; background: #000; border-radius: 12px; overflow: hidden; border: 4px solid var(--border); }
        #bgImg { width: 100%; height: 100%; object-fit: cover; transition: 0.3s; }
        .draggable { position: absolute; cursor: move; user-select: none; font-weight: 900; color: white; text-transform: uppercase; text-shadow: 3px 3px 0 #000; font-size: 55px; z-index: 50; }

        /* Contextual Toolbar Under Picture */
        .toolbar { width: 854px; display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 15px; background: var(--card); padding: 20px; margin-top: 10px; border-radius: 12px; border: 1px solid var(--border); }
        .tool-col { display: flex; flex-direction: column; gap: 10px; }
        .input-dark { padding:10px; background:#000; border:1px solid #333; color:#fff; border-radius:4px; font-size: 14px; width: 90%; }
        .btn { width: 100%; padding: 10px; background: #242b35; border: 1px solid var(--border); color: #fff; border-radius: 6px; cursor: pointer; font-weight: 800; font-size: 11px; }
        .btn:hover { border-color: var(--mint); color: var(--mint); }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div style="display:flex; align-items:center; justify-content:center; width:100%;">
        <form method="POST" action="/login" style="background:var(--card); padding:40px; border-radius:12px; border:1px solid var(--border); text-align:center;">
            <h2 style="color:var(--blue)">STUDIO ACCESS</h2>
            <input type="password" name="password" class="input-dark" placeholder="Enter Access Code" required><br><br>
            <button type="submit" class="btn" style="background:var(--mint); color:#000; font-size:14px;">ENTER WORKSPACE</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-header">HISTORY ARCHIVE</div>
        <div id="projectList"></div>
    </div>

    <div class="workspace">
        <input type="file" id="vidInp" style="display:none;" onchange="upload()">
        <button class="upload-btn" id="upBtn" onclick="document.getElementById('vidInp').click()">+ LOAD VIDEO (MAX 500MB)</button>
        
        <div id="status" class="status-box">Ready.</div>

        <div id="framesStrip" class="frames-strip"></div>

        <div class="canvas-wrap">
            <img id="bgImg" src="">
            <div id="textLayer" class="draggable">TEXT OVERLAY</div>
        </div>

        <div class="toolbar">
            <div class="tool-col">
                <input type="text" id="textInp" oninput="updateText()" placeholder="Type Headline..." class="input-dark">
                <div style="display:flex; gap:5px;">
                    <button class="btn" onclick="changeSize(8)">SIZE +</button>
                    <button class="btn" onclick="changeSize(-8)">SIZE -</button>
                </div>
            </div>
            <div class="tool-col">
                <button class="btn" onclick="zoom(1.8)">EMOTION ZOOM (1.8x)</button>
                <button class="btn" onclick="zoom(1)">RESET WORKSPACE</button>
            </div>
            <div class="tool-col">
                <button class="btn" style="background:var(--blue); color:#000; border:none;" onclick="alert('Syncing to YouTube Studio...')">🚀 SYNC TO YT</button>
                <button class="btn" onclick="window.print()">DOWNLOAD PNG</button>
            </div>
        </div>
    </div>
    {% endif %}

    <script>
        let textSize = 55;
        let active = null;
        let currentJob = null;

        // Draggable Text Logic
        document.addEventListener('mousedown', e => { if(e.target.id==='textLayer') { active=e.target; active.ox=e.clientX-active.offsetLeft; active.oy=e.clientY-active.offsetTop; } });
        document.addEventListener('mousemove', e => { if(active) { active.style.left=(e.clientX-active.ox)+'px'; active.style.top=(e.clientY-active.oy)+'px'; } });
        document.addEventListener('mouseup', () => active=null);

        function upload() {
            const file = document.getElementById('vidInp').files[0];
            if(!file) return;
            const fd = new FormData();
            fd.append('video', file);
            
            document.getElementById('status').innerText = "Uploading to Secure Cloud...";
            document.getElementById('upBtn').disabled = true;

            fetch('/process', { method: 'POST', body: fd })
                .then(r => r.json())
                .then(data => {
                    if(data.job_id) {
                        currentJob = data.job_id;
                        pollStatus();
                    } else { alert("Upload Failed: " + data.error); }
                });
        }

        function pollStatus() {
            if(!currentJob) return;
            fetch(`/status/${currentJob}`)
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'completed') {
                        document.getElementById('status').innerText = "Extraction Successful. Video Purged.";
                        renderFrames(data.frames);
                        loadVault();
                        document.getElementById('upBtn').disabled = false;
                    } else if (data.status === 'error') {
                        document.getElementById('status').innerText = "❌ FAILED: " + (data.details || "AI Error");
                        document.getElementById('upBtn').disabled = false;
                    } else {
                        document.getElementById('status').innerText = "AI Extracting 30 Frames... Please wait.";
                        setTimeout(pollStatus, 3000);
                    }
                });
        }

        function renderFrames(frames) {
            document.getElementById('framesStrip').innerHTML = frames.map(u => `
                <img src="${u}" class="thumb" onclick="setCanvas('${u}')">
            `).join('');
            if(frames.length > 0) setCanvas(frames[0]);
        }

        function setCanvas(url) { document.getElementById('bgImg').src = url; }
        
        async function loadVault() {
            const res = await fetch('/get_vault');
            const data = await res.json();
            document.getElementById('projectList').innerHTML = Object.keys(data).sort((a,b)=>b-a).map(n => `
                <div class="proj-item" onclick="openProj('${n}')">📁 History File #${n}</div>
            `).join('');
        }

        async function openProj(n) {
            const res = await fetch('/get_vault');
            const data = await res.json();
            renderFrames(data[n]);
        }

        function updateText() { document.getElementById('textLayer').innerText = document.getElementById('textInp').value; }
        function changeSize(v) { textSize += v; document.getElementById('textLayer').style.fontSize = textSize+'px'; }
        function zoom(s) { document.getElementById('bgImg').style.transform = `scale(${s})`; }

        {% if logged_in %} loadVault(); {% endif %}
    </script>
</body>
</html>
"""

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD:
        session['logged_in'] = True
    return redirect('/')

@app.route('/process', methods=['POST'])
def process():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    
    video = request.files['video']
    job_id = str(int(time.time()))
    jobs[job_id] = {'status': 'processing'}
    
    temp_fn = f"raw_{job_id}.mp4"
    
    try:
        # S3 Upload with Public ACL for AI access
        s3.upload_fileobj(
            video, BUCKET, temp_fn, 
            ExtraArgs={'ACL': 'public-read', 'ContentType': 'video/mp4'}
        )
        v_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{temp_fn}"
        
        # Trigger Non-blocking AI Extraction
        handler = fal_client.submit(
            "fal-ai/workflow-utilities/extract-nth-frame", 
            arguments={"video_url": v_url, "max_frames": 30}
        )
        
        # Monitor the job in a background thread to prevent timeout
        threading.Thread(target=background_monitor, args=(job_id, handler, temp_fn)).start()
        
        return jsonify({"job_id": job_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def background_monitor(jid, handler, s3_key):
    try:
        result = handler.get() # Wait for AI
        frames = [i['url'] for i in result.get('images', [])]
        
        # MECHANICAL NECESSITY: PURGE SOURCE VIDEO IMMEDIATELY AFTER EXTRACTION
        s3.delete_object(Bucket=BUCKET, Key=s3_key) 
        
        # Save Frames to History
        p_id = get_next_id()
        if not os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, "w") as f: json.dump({}, f)
            
        with open(PROJECTS_FILE, "r+") as f:
            vault_data = json.load(f)
            vault_data[p_id] = frames
            f.seek(0); json.dump(vault_data, f); f.truncate()
            
        jobs[jid] = {'status': 'completed', 'frames': frames}
    except Exception as e:
        print(f"FAILED: {str(e)}")
        jobs[jid] = {'status': 'error', 'details': str(e)}

@app.route('/status/<job_id>')
def status(job_id):
    return jsonify(jobs.get(job_id, {'status': 'not_found'}))

@app.route('/get_vault')
def get_vault():
    if not os.path.exists(PROJECTS_FILE): return jsonify({})
    with open(PROJECTS_FILE, "r") as f: return jsonify(json.load(f))

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
