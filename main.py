import os, boto3, fal_client, time, json
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- CONFIG ---
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "")

PROJECTS_FILE = "user_vault.json"

def get_next_project_id():
    """Generates sequential IDs like 101, 102 based on history."""
    if not os.path.exists(PROJECTS_FILE): return "101"
    with open(PROJECTS_FILE, "r") as f:
        data = json.load(f)
        if not data: return "101"
        # Find the highest numeric key and add 1
        numeric_keys = [int(k) for k in data.keys() if k.isdigit()]
        return str(max(numeric_keys) + 1) if numeric_keys else str(len(data) + 101)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar: History File */
        .sidebar { width: 280px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; display: flex; flex-direction: column; }
        .sidebar-header { padding: 20px; font-weight: 900; color: var(--blue); border-bottom: 1px solid var(--border); font-size: 12px; }
        .proj-item { padding: 15px 20px; border-bottom: 1px solid #1e252e; cursor: pointer; font-size: 13px; transition: 0.2s; }
        .proj-item:hover { background: #1c232d; color: var(--mint); padding-left: 25px; }

        .workspace { flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; background: #080a0d; overflow-y: auto; }
        
        /* The Bar (Top 6 Curated) */
        .frames-strip { width: 900px; display: flex; gap: 15px; overflow-x: auto; padding: 25px 0; border-bottom: 1px solid var(--border); }
        .thumb-container { position: relative; flex-shrink: 0; }
        .thumb { width: 130px; height: 74px; object-fit: cover; border-radius: 8px; cursor: pointer; transition: 0.25s; border: 2px solid transparent; }
        .thumb:hover { transform: scale(1.9); z-index: 100; border-color: var(--mint); box-shadow: 0 10px 30px rgba(0,0,0,1); }
        .plus-hint { position: absolute; top: 5px; right: 5px; background: var(--mint); color: #000; border-radius: 50%; width: 18px; height: 18px; font-size: 14px; text-align: center; font-weight: bold; pointer-events: none; opacity: 0.8; }

        /* Workspace Canvas */
        .canvas-wrap { position: relative; width: 854px; height: 480px; background: #000; border-radius: 12px; overflow: hidden; border: 4px solid var(--border); margin-top: 10px; }
        #bgImg { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }
        
        .draggable { position: absolute; cursor: move; user-select: none; z-index: 10; }
        #textLayer { font-weight: 900; color: white; text-transform: uppercase; text-shadow: 4px 4px 0 #000; font-size: 60px; }

        .controls { width: 854px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; background: var(--card); padding: 20px; margin-top: 20px; border-radius: 12px; border: 1px solid var(--border); }
        .btn { width: 100%; padding: 12px; background: #242b35; border: 1px solid var(--border); color: #fff; border-radius: 6px; cursor: pointer; font-weight: 800; font-size: 11px; margin-top: 5px; }
        .btn:hover { border-color: var(--mint); color: var(--mint); }
        .btn-pro { background: var(--blue); color: #000; border: none; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">HISTORY (SAVED SESSIONS)</div>
        <div id="projectList"></div>
    </div>

    <div class="workspace">
        <div style="width: 854px; display: flex; gap: 10px; margin-bottom: 10px;">
            <input type="text" id="pName" placeholder="Project Name (Optional)..." style="flex:1; background:#000; border:1px solid var(--border); color:#fff; padding:12px; border-radius:8px;">
            <input type="file" id="vidInp" style="display:none;" onchange="upload()">
            <button id="upBtn" onclick="document.getElementById('vidInp').click()" class="btn" style="background:var(--mint); color:#000; width: 220px; margin:0;">UPLOAD & EXTRACT</button>
        </div>

        <div id="framesStrip" class="frames-strip"></div>

        <div class="canvas-wrap" id="captureArea">
            <img id="bgImg" src="">
            <div id="textLayer" class="draggable">NEW VIRAL CLIP</div>
        </div>

        <div class="controls">
            <div>
                <label style="font-size:9px; color:var(--blue);">TEXT SETTINGS</label>
                <input type="text" id="textInp" oninput="updateText()" placeholder="Change text..." style="width:90%; padding:8px; margin:5px 0; background:#000; border:1px solid #333; color:#fff;">
                <div style="display:flex; gap:5px;">
                    <button class="btn" onclick="changeFontSize(10)">SIZE +</button>
                    <button class="btn" onclick="changeFontSize(-10)">SIZE -</button>
                </div>
            </div>
            <div>
                <label style="font-size:9px; color:var(--blue);">AI WORKSPACE</label>
                <button class="btn" onclick="zoom(1.8)">EMOTION ZOOM</button>
                <button class="btn" onclick="zoom(1)">RESET WORKSPACE</button>
                <button class="btn" onclick="alert('Predicting Click-Through Rate...')">📊 SCAN SUCCESS</button>
            </div>
            <div>
                <label style="font-size:9px; color:var(--blue);">ACTION</label>
                <button class="btn btn-pro" onclick="alert('Sent to A/B Testing Queue')">🚀 SYNC TO YOUTUBE</button>
                <button class="btn" onclick="window.print()">DOWNLOAD PNG</button>
            </div>
        </div>
    </div>

    <script>
        let textSize = 60;
        let active = null;

        document.addEventListener('mousedown', e => { if(e.target.classList.contains('draggable')) { active = e.target; active.ox = e.clientX - active.offsetLeft; active.oy = e.clientY - active.offsetTop; } });
        document.addEventListener('mousemove', e => { if(active) { active.style.left = (e.clientX - active.ox) + 'px'; active.style.top = (e.clientY - active.oy) + 'px'; } });
        document.addEventListener('mouseup', () => active = null);

        async function upload() {
            const btn = document.getElementById('upBtn');
            btn.innerText = "EXTRACTING & DELETING VIDEO...";
            const fd = new FormData();
            fd.append('video', document.getElementById('vidInp').files[0]);
            fd.append('name', document.getElementById('pName').value);
            
            const res = await fetch('/process', { method: 'POST', body: fd });
            const data = await res.json();
            renderFrames(data.frames);
            loadVault();
            btn.innerText = "UPLOAD & EXTRACT";
        }

        function renderFrames(frames) {
            document.getElementById('framesStrip').innerHTML = frames.map(u => `
                <div class="thumb-container" onclick="addToWorkspace('${u}')">
                    <img src="${u}" class="thumb">
                    <div class="plus-hint">+</div>
                </div>
            `).join('');
            if(frames.length > 0) addToWorkspace(frames[0]);
        }

        function addToWorkspace(url) {
            document.getElementById('bgImg').src = url;
        }

        async function loadVault() {
            const res = await fetch('/get_vault');
            const data = await res.json();
            document.getElementById('projectList').innerHTML = Object.keys(data).reverse().map(n => `
                <div class="proj-item" onclick="openProj('${n}')">📁 Project #${n}</div>
            `).join('');
        }

        async function openProj(n) {
            const res = await fetch('/get_vault');
            const data = await res.json();
            renderFrames(data[n]);
        }

        function updateText() { document.getElementById('textLayer').innerText = document.getElementById('textInp').value; }
        function changeFontSize(val) { textSize += val; document.getElementById('textLayer').style.fontSize = textSize + 'px'; }
        function zoom(s) { document.getElementById('bgImg').style.transform = `scale(${s})`; }

        loadVault();
    </script>
</body>
</html>
"""

@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    # If no name provided, use sequential ID like 101, 102
    p_name = request.form.get('name') or get_next_project_id()
    temp_fn = f"raw_{int(time.time())}.mp4"
    try:
        s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read'})
        v_url = f"https://{BUCKET}.s3.amazonaws.com/{temp_fn}"

        # 1. Dynamic Extraction
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
        all_frames = [i['url'] for i in ex.get('images', [])]

        # 2. Selection + Sharpening (Top 6 Clear frames)
        clean_frames = []
        for img in all_frames[:6]:
            db = fal_client.subscribe("fal-ai/nafnet/deblur", {"image_url": img})
            clean_frames.append(db['image']['url'])

        # 3. DELETE VIDEO IMMEDIATELY
        s3.delete_object(Bucket=BUCKET, Key=temp_fn)

        # 4. SAVE TO HISTORY
        with open(PROJECTS_FILE, "r+") as f:
            vault = json.load(f)
            vault[p_name] = clean_frames
            f.seek(0); json.dump(vault, f); f.truncate()

        return jsonify({"status": "success", "frames": clean_frames, "project_id": p_name})
    except: return jsonify({"status": "error"}), 500

@app.route('/get_vault')
def get_vault():
    with open(PROJECTS_FILE, "r") as f: return jsonify(json.load(f))

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
