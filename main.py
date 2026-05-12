import os, boto3, fal_client, time, json
from flask import Flask, request, jsonify, render_template_string, session, redirect

app = Flask(__name__)
app.secret_key = "studio_secret_key"

# --- INCREASE CAPACITY (2 GB LIMIT) ---
app.config['MAX_CONTENT_LENGTH'] = 2048 * 1024 * 1024 

# --- CONFIG ---
ACCESS_PASSWORD = "CREATOR_PRO_2026"
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "")

PROJECTS_FILE = "user_vault.json"

def get_next_id():
    if not os.path.exists(PROJECTS_FILE): return "101"
    with open(PROJECTS_FILE, "r") as f:
        try:
            data = json.load(f)
            nums = [int(k) for k in data.keys() if k.isdigit()]
            return str(max(nums) + 1) if nums else "101"
        except: return "101"

# Updated HTML with a Progress Bar for large 1GB+ files
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 280px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; }
        .sidebar-header { padding: 25px; font-weight: 900; color: var(--blue); border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
        .proj-item { padding: 15px 25px; border-bottom: 1px solid #1e252e; cursor: pointer; font-size: 13px; transition: 0.2s; color: #8a99af; }
        .proj-item:hover { background: #1c232d; color: var(--mint); }

        .workspace { flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; background: #080a0d; overflow-y: auto; }
        
        /* Progress Bar UI */
        .progress-container { width: 400px; height: 8px; background: #1e252e; border-radius: 10px; margin: 10px 0; display: none; overflow: hidden; }
        #progressBar { width: 0%; height: 100%; background: var(--mint); transition: width 0.1s; }

        .upload-btn { background: var(--mint); color: #000; padding: 12px 30px; border-radius: 50px; font-weight: 900; cursor: pointer; border: none; }
        .frames-strip { width: 950px; display: flex; gap: 12px; padding: 20px 0; overflow-x: auto; border-bottom: 1px solid var(--border); margin-bottom: 20px; min-height: 120px; }
        .thumb { width: 140px; height: 80px; object-fit: cover; border-radius: 6px; cursor: pointer; border: 2px solid transparent; }
        .thumb:hover { transform: scale(1.4); z-index: 10; border-color: var(--mint); }

        .canvas-wrap { position: relative; width: 854px; height: 480px; background: #000; border-radius: 12px; overflow: hidden; border: 4px solid var(--border); }
        #bgImg { width: 100%; height: 100%; object-fit: cover; }
        .draggable { position: absolute; cursor: move; user-select: none; font-weight: 900; color: white; text-transform: uppercase; text-shadow: 3px 3px 0 #000; font-size: 55px; }

        .context-toolbar { width: 854px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; background: var(--card); padding: 20px; margin-top: 10px; border-radius: 12px; border: 1px solid var(--border); }
        .input-dark { padding:10px; background:#000; border:1px solid #333; color:#fff; border-radius:4px; width: 90%; }
        .btn { width: 100%; padding: 10px; background: #242b35; border: 1px solid var(--border); color: #fff; border-radius: 6px; cursor: pointer; font-weight: 800; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div style="display:flex; align-items:center; justify-content:center; width:100%;">
        <form method="POST" action="/login" style="background:var(--card); padding:40px; border-radius:12px; text-align:center; border:1px solid var(--border);">
            <h2 style="color:var(--blue)">STUDIO LOGIN</h2>
            <input type="password" name="password" class="input-dark" placeholder="Access Code" required><br><br>
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
        <button class="upload-btn" id="upBtn" onclick="document.getElementById('vidInp').click()">+ UPLOAD LARGE VIDEO (1GB+)</button>
        
        <div class="progress-container" id="pCont"><div id="progressBar"></div></div>
        <div id="statusText" style="font-size: 11px; color: var(--blue); margin-bottom: 10px;"></div>

        <div id="framesStrip" class="frames-strip"></div>

        <div class="canvas-wrap">
            <img id="bgImg" src="">
            <div id="textLayer" class="draggable" id="dragText">EDIT HOOK</div>
        </div>

        <div class="context-toolbar">
            <div style="display:flex; flex-direction:column; gap:10px;">
                <input type="text" id="textInp" oninput="updateText()" placeholder="Type here..." class="input-dark">
                <button class="btn" onclick="changeSize(10)">SIZE +</button>
            </div>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <button class="btn" onclick="zoom(1.8)">ZOOM 1.8x</button>
                <button class="btn" onclick="zoom(1)">RESET</button>
            </div>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <button class="btn" style="background:var(--blue); color:#000;" onclick="alert('Syncing...')">SYNC TO YT</button>
                <button class="btn" onclick="window.print()">DOWNLOAD PNG</button>
            </div>
        </div>
    </div>
    {% endif %}

    <script>
        let textSize = 55;
        let active = null;

        document.addEventListener('mousedown', e => { if(e.target.id==='textLayer') { active=e.target; active.ox=e.clientX-active.offsetLeft; active.oy=e.clientY-active.offsetTop; } });
        document.addEventListener('mousemove', e => { if(active) { active.style.left=(e.clientX-active.ox)+'px'; active.style.top=(e.clientY-active.oy)+'px'; } });
        document.addEventListener('mouseup', () => active=null);

        function upload() {
            const file = document.getElementById('vidInp').files[0];
            const xhr = new XMLHttpRequest();
            const fd = new FormData();
            
            document.getElementById('pCont').style.display = 'block';
            document.getElementById('upBtn').disabled = true;
            document.getElementById('statusText').innerText = "Uploading to Secure Vault...";

            fd.append('video', file);

            xhr.upload.addEventListener('progress', e => {
                const percent = (e.loaded / e.total) * 100;
                document.getElementById('progressBar').style.width = percent + '%';
            });

            xhr.onreadystatechange = function() {
                if (xhr.readyState == 4 && xhr.status == 200) {
                    const data = JSON.parse(xhr.responseText);
                    document.getElementById('statusText').innerText = "Extraction Complete. Video Purged.";
                    renderFrames(data.frames);
                    loadVault();
                    document.getElementById('pCont').style.display = 'none';
                    document.getElementById('upBtn').disabled = false;
                }
            };

            xhr.open('POST', '/process', true);
            xhr.send(fd);
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
                <div class="proj-item" onclick="openProj('${n}')">📁 History #${n} (30 Frames)</div>
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
    p_id = get_next_id()
    temp_fn = f"large_raw_{int(time.time())}.mp4"
    
    try:
        # High-Speed S3 Transfer
        s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read'})
        v_url = f"https://{BUCKET}.s3.amazonaws.com/{temp_fn}"

        # AI Extraction (30 Frames)
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
        frames = [i['url'] for i in ex.get('images', [])]

        # PURGE VIDEO IMMEDIATELY (Privacy + Space Rule)
        s3.delete_object(Bucket=BUCKET, Key=temp_fn)

        # Save to History
        with open(PROJECTS_FILE, "r+") as f:
            vault = json.load(f)
            vault[p_id] = frames
            f.seek(0); json.dump(vault, f); f.truncate()

        return jsonify({"status": "success", "frames": frames})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_vault')
def get_vault():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    if not os.path.exists(PROJECTS_FILE): return jsonify({})
    with open(PROJECTS_FILE, "r") as f: return jsonify(json.load(f))

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)q
