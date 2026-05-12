import os, boto3, fal_client, time, json, logging
from flask import Flask, request, jsonify, render_template_string

# --- SETUP LOGGING (To see why it crashed) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- CONFIGURATION (Crucial!) ---
# Ensure these are set in your Environment Variables or replace the strings below
FAL_KEY = os.environ.get("FAL_KEY", "your-key-here")
AWS_ACCESS = os.environ.get("AWS_ACCESS_KEY_ID", "your-access-key")
AWS_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY", "your-secret-key")
BUCKET = os.environ.get("AWS_BUCKET_NAME", "your-bucket-name")

os.environ["FAL_KEY"] = FAL_KEY

# Initialize S3 safely
try:
    s3 = boto3.client('s3', 
                      aws_access_key_id=AWS_ACCESS, 
                      aws_secret_access_key=AWS_SECRET, 
                      region_name='eu-north-1')
except Exception as e:
    logger.error(f"S3 Connection Failed: {e}")

PROJECTS_FILE = "user_vault.json"
if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, "w") as f: json.dump({}, f)

# --- RECOVERY LOGIC ---
def safe_load_vault():
    try:
        with open(PROJECTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# --- HTML UI (Simplified for Stability) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ViralFrame V31 - Stable</title>
    <style>
        body { background: #0B0D10; color: white; font-family: sans-serif; display: flex; margin: 0; }
        .sidebar { width: 250px; background: #151A21; height: 100vh; border-right: 1px solid #273140; padding: 20px; }
        .main { flex: 1; padding: 40px; display: flex; flex-direction: column; align-items: center; }
        .canvas { width: 854px; height: 480px; background: #000; border: 2px solid #40E0FF; position: relative; overflow: hidden; }
        #mainImg { width: 100%; height: 100%; object-fit: cover; }
        .controls { margin-top: 20px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; width: 854px; }
        .btn { background: #00FFC2; color: black; border: none; padding: 15px; font-weight: bold; cursor: pointer; border-radius: 5px; }
        .btn-sync { background: #40E0FF; }
        .strip { display: flex; gap: 10px; margin-bottom: 20px; overflow-x: auto; width: 854px; }
        .thumb { width: 100px; height: 60px; object-fit: cover; cursor: pointer; opacity: 0.6; }
        .thumb:hover { opacity: 1; border: 2px solid #00FFC2; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3>PROJECT BAR</h3>
        <div id="projectList"></div>
    </div>
    <div class="main">
        <div style="margin-bottom: 20px;">
            <input type="text" id="pName" placeholder="Project Name">
            <input type="file" id="vidInp">
            <button class="btn" onclick="upload()">EXTRACT & DELETE VIDEO</button>
        </div>
        <div id="frameStrip" class="strip"></div>
        <div class="canvas">
            <img id="mainImg" src="">
        </div>
        <div class="controls">
            <button class="btn" onclick="zoom(1.8)">EMOTION ZOOM</button>
            <button class="btn" onclick="zoom(1)">RESET</button>
            <button class="btn btn-sync" onclick="alert('Syncing A/B Test to YouTube API...')">SYNC TO YOUTUBE</button>
        </div>
    </div>

    <script>
        async function upload() {
            const btn = document.querySelector('.btn');
            btn.innerText = "PROCESSING...";
            const fd = new FormData();
            fd.append('video', document.getElementById('vidInp').files[0]);
            fd.append('name', document.getElementById('pName').value || "Untitled");

            try {
                const res = await fetch('/process', { method: 'POST', body: fd });
                const data = await res.json();
                renderFrames(data.frames);
                loadVault();
            } catch (e) { alert("Upload Failed. Check console."); }
            btn.innerText = "EXTRACT & DELETE VIDEO";
        }

        function renderFrames(frames) {
            document.getElementById('frameStrip').innerHTML = frames.map(u => `
                <img src="${u}" class="thumb" onclick="document.getElementById('mainImg').src='${u}'">
            `).join('');
            document.getElementById('mainImg').src = frames[0];
        }

        async function loadVault() {
            const res = await fetch('/get_vault');
            const data = await res.json();
            document.getElementById('projectList').innerHTML = Object.keys(data).map(n => `
                <div style="padding:10px; cursor:pointer;" onclick="renderFramesByProject('${n}')">🎬 ${n}</div>
            `).join('');
        }

        function zoom(s) { document.getElementById('mainImg').style.transform = `scale(${s})`; }
        
        loadVault();
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE)

@app.route('/get_vault')
def get_vault(): return jsonify(safe_load_vault())

@app.route('/process', methods=['POST'])
def process():
    if 'video' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    video = request.files['video']
    name = request.form.get('name', 'Project')
    temp_fn = f"raw_{int(time.time())}.mp4"

    try:
        logger.info(f"Starting upload for {name}...")
        # 1. Upload to S3
        s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read'})
        v_url = f"https://{BUCKET}.s3.amazonaws.com/{temp_fn}"

        # 2. Extract
        logger.info("Extracting frames via FAL...")
        handler = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {
            "video_url": v_url, "max_frames": 12
        })
        frames = [img['url'] for img in handler.get('images', [])]

        # 3. DELETE VIDEO (Privacy & Cost)
        logger.info("Deleting raw video from S3...")
        s3.delete_object(Bucket=BUCKET, Key=temp_fn)

        # 4. Save Image URLs to Project Bar
        vault = safe_load_vault()
        vault[name] = frames
        with open(PROJECTS_FILE, "w") as f: json.dump(vault, f)

        return jsonify({"status": "success", "frames": frames})
    except Exception as e:
        logger.error(f"CRASH: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
