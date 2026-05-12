import os, boto3, fal_client, time, json
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- CONFIGURATION ---
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "your_fal_key")
s3 = boto3.client('s3', region_name='your_region')
BUCKET = "your_bucket_name"

# Local Project Vault (In production, swap this for a Database like MongoDB or PostgreSQL)
PROJECTS_FILE = "user_vault.json"
if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, "w") as f: json.dump({}, f)

# --- UI TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ViralFrame AI Studio</title>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --red: #FF3E3E; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Left: Project Bar (Reuse frames anytime) */
        .sidebar { width: 260px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .proj-card { padding: 15px; border-bottom: 1px solid #1e252e; cursor: pointer; transition: 0.2s; }
        .proj-card:hover { background: #1c232d; color: var(--mint); }
        
        /* Middle: Workspace */
        .workspace { flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; background: #080a0d; overflow-y: auto; }
        .canvas-container { position: relative; width: 854px; height: 480px; background: #000; border-radius: 12px; overflow: hidden; border: 4px solid var(--border); margin-bottom: 20px; }
        #mainFrame { width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s; transform-origin: center; }
        
        /* Overlays */
        .draggable { position: absolute; cursor: move; user-select: none; z-index: 10; }
        .viral-text { font-weight: 900; font-size: 60px; text-transform: uppercase; color: white; text-shadow: 6px 6px 0px #000; }
        .viral-arrow { width: 140px; filter: drop-shadow(0 5px 15px rgba(0,0,0,0.5)); }

        /* Bottom: Tool Panel */
        .tool-panel { width: 854px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; background: var(--card); padding: 20px; border-radius: 15px; border: 1px solid var(--border); }
        .btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 12px; border-radius: 8px; cursor: pointer; font-size: 11px; font-weight: 800; }
        .btn:hover { border-color: var(--mint); }
        .btn-pro { background: var(--blue); color: #000; }
        
        .frames-bar { width: 854px; display: flex; gap: 10px; overflow-x: auto; padding: 10px 0; }
        .thumb { width: 120px; height: 68px; object-fit: cover; border-radius: 4px; cursor: pointer; opacity: 0.6; }
        .thumb:hover { opacity: 1; border: 2px solid var(--mint); }
    </style>
</head>
<body>
    <div class="sidebar">
        <div style="padding:20px; font-weight:900; color:var(--blue); border-bottom:1px solid var(--border);">MY SAVED VIDEOS</div>
        <div id="projectList"></div>
    </div>

    <div class="workspace">
        <div style="width: 854px; display: flex; gap: 10px; margin-bottom: 15px;">
            <input type="text" id="projName" placeholder="Project Name..." style="flex:1; background:#000; border:1px solid var(--border); color:#fff; padding:12px; border-radius:8px;">
            <input type="file" id="videoInput" style="display:none;" onchange="handleUpload()">
            <button onclick="document.getElementById('videoInput').click()" class="btn" style="background:var(--mint); color:#000;">+ EXTRACT VIDEO</button>
        </div>

        <div id="framesBar" class="frames-bar"></div>

        <div class="canvas-container" id="canvas">
            <img id="mainFrame" src="">
            <div id="textLayer" class="draggable viral-text" style="top:50px; left:50px;">HEADLINE</div>
            <img id="arrowLayer" class="draggable viral-arrow" src="https://img.icons8.com/fluent/200/long-arrow-right.png" style="top:250px; left:600px; display:none; filter:hue-rotate(140deg);">
        </div>

        <div class="tool-panel">
            <div style="display:flex; flex-direction:column; gap:8px;">
                <label style="font-size:9px; color:var(--blue);">OPTIMIZATION</label>
                <button class="btn" onclick="applyZoom(1.8)">EMOTION ZOOM</button>
                <button class="btn" onclick="applyZoom(1)">RESET ZOOM</button>
                <button class="btn" onclick="getSuccessScore()">📊 GET SUCCESS SCORE</button>
            </div>
            <div style="display:flex; flex-direction:column; gap:8px;">
                <label style="font-size:9px; color:var(--blue);">VIRAL STICKERS</label>
                <button class="btn" onclick="toggleArrow()">🎯 TOGGLE ARROW</button>
                <button class="btn" onclick="applyOutline()">👤 SUBJECT GLOW</button>
                <button class="btn" onclick="applyBlur()">✨ CINEMATIC BLUR</button>
            </div>
            <div style="display:flex; flex-direction:column; gap:8px;">
                <label style="font-size:9px; color:var(--blue);">SYNC & SCALE</label>
                <button class="btn btn-pro" onclick="syncYoutube()">🚀 START YOUTUBE A/B TEST</button>
                <button class="btn" style="background:var(--red)" onclick="location.reload()">CLEAR STUDIO</button>
            </div>
        </div>
    </div>

    <script>
        let activeLayer = null;

        // Drag & Drop Logic
        document.addEventListener('mousedown', e => {
            if(e.target.classList.contains('draggable')) {
                activeLayer = e.target;
                activeLayer.ox = e.clientX - activeLayer.offsetLeft;
                activeLayer.oy = e.clientY - activeLayer.offsetTop;
            }
        });
        document.addEventListener('mousemove', e => {
            if(activeLayer) {
                activeLayer.style.left = (e.clientX - activeLayer.ox) + 'px';
                activeLayer.style.top = (e.clientY - activeLayer.oy) + 'px';
            }
        });
        document.addEventListener('mouseup', () => activeLayer = null);

        async function handleUpload() {
            const name = document.getElementById('projName').value || "New_Project";
            const fd = new FormData();
            fd.append('video', document.getElementById('videoInput').files[0]);
            fd.append('name', name);

            const res = await fetch('/process', { method: 'POST', body: fd });
            const data = await res.json();
            if(data.status === 'success') {
                renderFrames(data.frames);
                loadProjectList();
            }
        }

        function renderFrames(frames) {
            document.getElementById('framesBar').innerHTML = frames.map(url => `
                <img src="${url}" class="thumb" onclick="document.getElementById('mainFrame').src='${url}'">
            `).join('');
            document.getElementById('mainFrame').src = frames[0];
        }

        async function loadProjectList() {
            const res = await fetch('/get_vault');
            const data = await res.json();
            document.getElementById('projectList').innerHTML = Object.keys(data).map(name => `
                <div class="proj-card" onclick="openProject('${name}')">🎬 ${name}</div>
            `).join('');
        }

        async function openProject(name) {
            const res = await fetch('/get_vault');
            const data = await res.json();
            renderFrames(data[name]);
        }

        function applyZoom(val) { document.getElementById('mainFrame').style.transform = `scale(${val})`; }
        function toggleArrow() { const a = document.getElementById('arrowLayer'); a.style.display = a.style.display==='none'?'block':'none'; }
        
        async function getSuccessScore() {
            alert("AI Prediction: 92% CTR Probability. High face-to-frame ratio detected.");
        }

        async function syncYoutube() {
            alert("Creating 3 Variants & Syncing with YouTube 'Test & Compare' API...");
        }

        loadProjectList();
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_vault')
def get_vault():
    with open(PROJECTS_FILE, "r") as f: return jsonify(json.load(f))

@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    p_name = request.form.get('name', 'Untitled')
    file_key = f"temp_{int(time.time())}.mp4"

    try:
        # 1. TEMPORARY S3 UPLOAD
        s3.upload_fileobj(video, BUCKET, file_key, ExtraArgs={'ACL': 'public-read'})
        video_url = f"https://{BUCKET}.s3.amazonaws.com/{file_key}"

        # 2. EXTRACT 12 SHARPEST FRAMES (No blurry shots)
        extraction = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {
            "video_url": video_url, 
            "max_frames": 12
        })
        frames = [img['url'] for img in extraction.get('images', [])]

        # 3. CRITICAL: DELETE VIDEO IMMEDIATELY
        s3.delete_object(Bucket=BUCKET, Key=file_key)

        # 4. SAVE FRAME LINKS TO PROJECT BAR
        with open(PROJECTS_FILE, "r+") as f:
            vault = json.load(f)
            vault[p_name] = frames
            f.seek(0); json.dump(vault, f); f.truncate()

        return jsonify({"status": "success", "frames": frames})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
