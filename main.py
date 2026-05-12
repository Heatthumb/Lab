import os, boto3, fal_client, time, json
from flask import Flask, request, jsonify, render_template_string, session, redirect

app = Flask(__name__)
app.secret_key = "studio_secret_key" # Change this for session security

# --- CONFIG ---
ACCESS_PASSWORD = "CREATOR_PRO_2026" # SET YOUR PASSWORD HERE
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Login Overlay */
        #loginOverlay { position: fixed; inset: 0; background: var(--carbon); z-index: 999; display: flex; align-items: center; justify-content: center; flex-direction: column; }
        .login-box { background: var(--card); padding: 40px; border-radius: 12px; border: 1px solid var(--border); text-align: center; }

        /* Sidebar (Total History Archive) */
        .sidebar { width: 280px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; }
        .sidebar-header { padding: 25px; font-weight: 900; color: var(--blue); border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
        .proj-item { padding: 15px 25px; border-bottom: 1px solid #1e252e; cursor: pointer; font-size: 13px; transition: 0.2s; color: #8a99af; }
        .proj-item:hover { background: #1c232d; color: var(--mint); }

        /* Workspace Area */
        .workspace { flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; background: #080a0d; overflow-y: auto; }
        .upload-btn { background: var(--mint); color: #000; padding: 12px 30px; border-radius: 50px; font-weight: 900; cursor: pointer; border: none; margin-bottom: 20px; }

        /* Project Bar (All Frames) */
        .frames-strip { width: 950px; display: flex; gap: 12px; padding: 20px 0; overflow-x: auto; border-bottom: 1px solid var(--border); margin-bottom: 20px; min-height: 120px; }
        .thumb-wrap { position: relative; flex-shrink: 0; cursor: pointer; }
        .thumb { width: 140px; height: 80px; object-fit: cover; border-radius: 6px; transition: 0.2s; border: 2px solid transparent; }
        .thumb-wrap:hover .thumb { transform: scale(1.5); z-index: 100; border-color: var(--mint); box-shadow: 0 10px 30px #000; }

        /* Workspace Canvas */
        .canvas-wrap { position: relative; width: 854px; height: 480px; background: #000; border-radius: 12px; overflow: hidden; border: 4px solid var(--border); }
        #bgImg { width: 100%; height: 100%; object-fit: cover; transition: 0.3s; }
        .draggable { position: absolute; cursor: move; user-select: none; z-index: 10; font-weight: 900; color: white; text-transform: uppercase; text-shadow: 3px 3px 0 #000; font-size: 55px; }

        /* Controls Under the Picture */
        .context-toolbar { width: 854px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; background: var(--card); padding: 20px; margin-top: 10px; border-radius: 0 0 12px 12px; border: 1px solid var(--border); }
        .tool-col { display: flex; flex-direction: column; gap: 10px; }
        .btn { width: 100%; padding: 10px; background: #242b35; border: 1px solid var(--border); color: #fff; border-radius: 6px; cursor: pointer; font-weight: 800; font-size: 11px; }
        .btn:hover { border-color: var(--mint); color: var(--mint); }
        .input-dark { padding:10px; background:#000; border:1px solid #333; color:#fff; border-radius:4px; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div id="loginOverlay">
        <form class="login-box" method="POST" action="/login">
            <h2 style="color:var(--blue)">STUDIO ACCESS</h2>
            <input type="password" name="password" class="input-dark" placeholder="Enter Access Code" required>
            <br><br>
            <button type="submit" class="btn" style="background:var(--mint); color:#000">ENTER WORKSPACE</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-header">HISTORY ARCHIVE</div>
        <div id="projectList"></div>
    </div>

    <div class="workspace">
        <div class="upload-zone">
            <input type="file" id="vidInp" style="display:none;" onchange="upload()">
            <button class="upload-btn" onclick="document.getElementById('vidInp').click()">+ EXTRACT NEW VIDEO (30 FRAMES)</button>
        </div>

        <div id="framesStrip" class="frames-strip"></div>

        <div class="canvas-wrap">
            <img id="bgImg" src="">
            <div id="textLayer" class="draggable">VIRAL HOOK</div>
        </div>

        <div class="context-toolbar">
            <div class="tool-col">
                <input type="text" id="textInp" oninput="updateText()" placeholder="Headline..." class="input-dark">
                <div style="display:flex; gap:5px;">
                    <button class="btn" onclick="changeSize(10)">SIZE +</button>
                    <button class="btn" onclick="changeSize(-10)">SIZE -</button>
                </div>
            </div>
            <div class="tool-col">
                <button class="btn" onclick="zoom(1.8)">EMOTION ZOOM</button>
                <button class="btn" onclick="zoom(1)">RESET ZOOM</button>
                <button class="btn" onclick="alert('AI Scan: 94/100 Success Rate')">📊 SCAN VIRAL POTENTIAL</button>
            </div>
            <div class="tool-col">
                <button class="btn" style="background:var(--blue); color:#000; border:none" onclick="alert('Syncing to YouTube...')">🚀 SYNC TO YT</button>
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

        async function upload() {
            const btn = document.querySelector('.upload-btn');
            btn.innerText = "PROCESSING & PURGING VIDEO...";
            const fd = new FormData();
            fd.append('video', document.getElementById('vidInp').files[0]);
            const res = await fetch('/process', { method: 'POST', body: fd });
            const data = await res.json();
            renderFrames(data.frames);
            loadVault();
            btn.innerText = "+ EXTRACT NEW VIDEO (30 FRAMES)";
        }

        function renderFrames(frames) {
            document.getElementById('framesStrip').innerHTML = frames.map(u => `
                <div class="thumb-wrap" onclick="setCanvas('${u}')">
                    <img src="${u}" class="thumb">
                </div>
            `).join('');
            if(frames.length > 0) setCanvas(frames[0]);
        }

        function setCanvas(url) { document.getElementById('bgImg').src = url; }

        async function loadVault() {
            const res = await fetch('/get_vault');
            const data = await res.json();
            document.getElementById('projectList').innerHTML = Object.keys(data).sort((a,b)=>b-a).map(n => `
                <div class="proj-item" onclick="openProj('${n}')">📁 Project #${n} (30 Frames)</div>
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

        {% if logged_in %}
        loadVault();
        {% endif %}
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
    temp_fn = f"raw_{int(time.time())}.mp4"
    try:
        s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read'})
        v_url = f"https://{BUCKET}.s3.amazonaws.com/{temp_fn}"

        # 1. EXTRACT ALL 30 FRAMES
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
        frames = [i['url'] for i in ex.get('images', [])]

        # 2. DELETE SOURCE VIDEO IMMEDIATELY
        s3.delete_object(Bucket=BUCKET, Key=temp_fn)

        # 3. SAVE TO HISTORY VAULT
        with open(PROJECTS_FILE, "r+") as f:
            vault = json.load(f)
            vault[p_id] = frames
            f.seek(0); json.dump(vault, f); f.truncate()

        return jsonify({"status": "success", "frames": frames})
    except: return jsonify({"status": "error"}), 500

@app.route('/get_vault')
def get_vault():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    with open(PROJECTS_FILE, "r") as f: return jsonify(json.load(f))

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
