import os, boto3, fal_client, time
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- CONFIG ---
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
LAB_PASSWORD = os.environ.get("LAB_PASSWORD", "HEATHUMB2026")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "heatthumb-vault-sruli-259851212536-eu-north-1-an")

# --- STUDIO UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --red: #FF3E3E; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 300px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .workspace { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; align-items: center; background: #080a0d; }
        
        /* The Design Canvas */
        .canvas-wrap { 
            position: relative; width: 854px; height: 480px; 
            background: #000; border-radius: 12px; overflow: hidden; 
            border: 6px solid transparent; box-shadow: 0 30px 60px rgba(0,0,0,0.6); 
            margin-bottom: 25px; 
        }
        
        /* Image Layer with Virtual Zoom */
        #bgImg { 
            width: 100%; height: 100%; object-fit: cover; 
            transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            transform-origin: center; 
        }
        
        /* Draggable Overlay System */
        .draggable { position: absolute; cursor: move; user-select: none; z-index: 10; }
        .text-layer { font-weight: 900; font-size: 60px; text-transform: uppercase; white-space: nowrap; line-height: 1; pointer-events: auto; }
        .arrow-layer { width: 140px; filter: drop-shadow(0 5px 15px rgba(0,0,0,0.5)); pointer-events: auto; }

        .pro-panel { width: 854px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; background: var(--card); padding: 20px; border-radius: 20px; border: 1px solid var(--border); }
        .control-box { display: flex; flex-direction: column; gap: 8px; }
        label { font-size: 9px; font-weight: bold; color: #8A94A6; text-transform: uppercase; letter-spacing: 1px; }
        
        .btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 10px; font-weight: 800; }
        .btn:hover { border-color: var(--mint); background: #2d3642; }
        .btn-active { background: var(--blue); color: #000; }

        input[type="text"] { background: #000; border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 8px; font-size: 12px; }
        .lib-thumb { width: 100%; border-radius: 8px; margin-bottom: 10px; cursor: pointer; opacity: 0.6; transition: 0.2s; }
        .lib-thumb:hover { opacity: 1; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div style="padding:20px; font-weight:900; color:var(--blue); border-bottom:1px solid var(--border); font-size: 12px;">RAW VIDEO FRAMES</div>
        <div id="library" style="padding:15px; overflow-y:auto;"></div>
    </div>

    <div class="workspace">
        <div style="margin-bottom:20px; display:flex; gap:10px;">
            <input type="file" id="videoFile">
            <button onclick="processVideo()" class="btn" style="background:var(--mint); color:#000; padding: 0 20px;">CURATE VIDEO</button>
        </div>

        <div class="canvas-wrap" id="canvas">
            <img id="bgImg" src="">
            <div id="textObj" class="draggable text-layer" style="top:50px; left:50px; color:#ffffff;">EMOTION!</div>
            <img id="arrowObj" class="draggable arrow-layer" src="https://img.icons8.com/fluent/200/long-arrow-right.png" style="top:250px; left:600px; display:none; filter: hue-rotate(140deg) saturate(5);">
        </div>

        <div class="pro-panel">
            <div class="control-box">
                <label>Face & Emotion Zoom</label>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:5px;">
                    <button class="btn" onclick="setZoom(1)">Normal View</button>
                    <button class="btn" onclick="setZoom(1.8)">Face Zoom (1.8x)</button>
                    <button class="btn" onclick="setZoom(2.5)">Extreme (2.5x)</button>
                    <button class="btn" onclick="resetPos()">Reset Center</button>
                </div>
                <input type="text" id="textInp" placeholder="Enter headline..." oninput="updateText()">
            </div>

            <div class="control-box">
                <label>Viral Layers (Stickers)</label>
                <button class="btn" onclick="toggleArrow()">🎯 ADD VIRAL ARROW</button>
                <button class="btn" onclick="applyOutline()">👤 SUBJECT GLOW (WHITE)</button>
                <div style="display:flex; gap:5px;">
                    <input type="color" id="textColor" value="#ffffff" onchange="updateStyles()">
                    <input type="color" id="borderColor" value="#00FFC2" onchange="updateStyles()">
                    <button class="btn" onclick="applyPortrait()">✨ BLUR BG</button>
                </div>
            </div>

            <div class="control-box">
                <label>Export Final</label>
                <button class="btn" style="background:var(--blue); color:#000; font-size:12px;" onclick="alert('Exporting 4K Thumbnail Package...')">DOWNLOAD FOR YOUTUBE</button>
                <button class="btn" style="color:var(--red)" onclick="location.reload()">START NEW VIDEO</button>
                <p style="font-size:8px; color:#555; margin-top:5px;">*No AI used for Zoom, Arrows, or Text. Image quality remains raw.</p>
            </div>
        </div>
    </div>

    <script>
        let active = null;
        let currentZoom = 1;

        document.addEventListener('mousedown', e => {
            if(e.target.classList.contains('draggable')) {
                active = e.target;
                active.offsetX = e.clientX - active.offsetLeft;
                active.offsetY = e.clientY - active.offsetTop;
            }
        });
        document.addEventListener('mousemove', e => {
            if(active) {
                active.style.left = (e.clientX - active.offsetX) + 'px';
                active.style.top = (e.clientY - active.offsetY) + 'px';
            }
        });
        document.addEventListener('mouseup', () => active = null);

        async function processVideo() {
            const fd = new FormData(); fd.append('video', document.getElementById('videoFile').files[0]);
            const res = await fetch('/process', { method: 'POST', body: fd });
            const data = await res.json();
            if(data.status === 'success') {
                document.getElementById('library').innerHTML = data.library.map(u => `<img src="${u}" class="lib-thumb" onclick="setBg('${u}')">`).join('');
                setBg(data.pack[0]);
            }
        }

        function setBg(u) { document.getElementById('bgImg').src = u; setZoom(1); }
        function setZoom(val) { currentZoom = val; document.getElementById('bgImg').style.transform = `scale(${val})`; }
        function resetPos() { document.getElementById('bgImg').style.objectPosition = 'center'; }
        
        function updateText() { document.getElementById('textObj').innerText = document.getElementById('textInp').value; }
        
        function toggleArrow() {
            const arrow = document.getElementById('arrowObj');
            arrow.style.display = arrow.style.display === 'none' ? 'block' : 'none';
        }

        function applyOutline() {
            const img = document.getElementById('bgImg');
            img.style.filter = img.style.filter.includes('drop-shadow') ? 'none' : 'drop-shadow(0 0 15px white) brightness(1.05)';
        }

        function updateStyles() {
            const t = document.getElementById('textObj');
            const c = document.getElementById('canvas');
            t.style.color = document.getElementById('textColor').value;
            c.style.borderColor = document.getElementById('borderColor').value;
            t.style.textShadow = '5px 5px 0px #000';
        }

        async function applyPortrait() {
            const img = document.getElementById('bgImg');
            const res = await fetch('/portrait', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ url: img.src }) });
            const d = await res.json();
            if(d.url) img.src = d.url;
        }
    </script>
</body>
</html>
"""

@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    fn = f"v_{int(time.time())}.mp4"
    try:
        s3.upload_fileobj(video, BUCKET, fn, ExtraArgs={'ACL': 'public-read'})
        v_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{fn}"
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 15})
        raw_frames = list(dict.fromkeys([i['url'] for i in ex.get('images', [])]))
        s3.delete_object(Bucket=BUCKET, Key=fn)
        return jsonify({"status": "success", "pack": raw_frames[2:8], "library": raw_frames})
    except Exception: return jsonify({"status": "error"}), 500

@app.route('/portrait', methods=['POST'])
def portrait():
    d = request.json
    r = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": d['url'],
        "prompt": "Keep the main central subject/person perfectly sharp. Apply a professional cinematic heavy background blur with bokeh. High-end video still.",
        "strength": 0.28
    })
    return jsonify({"url": r['images'][0]['url']})

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
