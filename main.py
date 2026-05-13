import os, boto3, fal_client, time, json, threading, random
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "studio_v55_hover"
ACCESS_PASSWORD = "Heathumb2026"

# Cloud & S3 Logic
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "")
jobs = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --pink: #FF007A; --red: #ff4d4d; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow:hidden; }
        
        /* Sidebar */
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; display: flex; flex-direction: column; }
        .sidebar-sec { padding: 15px; border-bottom: 1px solid var(--border); }
        .section-title { font-size: 10px; font-weight: 900; color: var(--blue); text-transform: uppercase; margin-bottom: 10px; }
        
        .frame-bank { padding: 10px; display: grid; grid-template-columns: 1fr; gap: 12px; }
        .bank-item { position: relative; border-radius: 6px; overflow: hidden; border: 1px solid #333; }
        .bank-img { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }
        
        .icon-btn { position: absolute; border: none; border-radius: 4px; width: 24px; height: 24px; cursor: pointer; font-weight: 900; z-index: 10; display: flex; align-items: center; justify-content: center; }
        .add-btn { top: 5px; right: 5px; background: var(--mint); color: #000; }
        .del-btn-small { top: 5px; left: 5px; background: var(--red); color: #fff; }

        /* Workspace */
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 40px; max-width: 1400px; margin: 0 auto; }

        /* Card & NEW Hover Preview Logic */
        .editor-card { background: var(--card); border-radius: 12px; padding: 15px; border: 1px solid var(--border); position: relative; }
        
        .canvas-container { position: relative; width: 100%; aspect-ratio: 16/9; transition: transform 0.3s ease; z-index: 1; }
        
        /* THE FIX: When hovering, the image pops out clearly without a modal */
        .canvas-container:hover { 
            transform: scale(1.15); 
            z-index: 100; 
            box-shadow: 0 20px 50px rgba(0,0,0,0.8);
            cursor: crosshair;
        }

        .canvas-area { 
            position: relative; width: 100%; height: 100%; 
            background: #000; overflow: hidden; border-radius: 8px; 
            border: 0px solid transparent; 
        }
        
        .bg-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 1; }
        .subject-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 2; pointer-events: none; }
        .sticker-mode { filter: drop-shadow(0 0 12px rgba(255,255,255,0.9)) drop-shadow(0 0 2px #fff); }

        .card-delete { position: absolute; top: -10px; right: -10px; background: var(--red); color: white; border: none; width: 28px; height: 28px; border-radius: 50%; font-weight: 900; cursor: pointer; z-index: 20; border: 2px solid var(--carbon); }

        .drag-item { position: absolute; cursor: move; z-index: 10; user-select: none; }
        .overlay-text { font-weight: 900; text-transform: uppercase; white-space: nowrap; padding: 5px; text-shadow: 2px 2px 10px #000; font-size: 24px; }

        .card-controls { margin-top: 15px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .c-btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 10px; font-size: 11px; cursor: pointer; border-radius: 6px; font-weight: 700; }
        
        .export-box { grid-column: span 3; display: flex; gap: 8px; margin-top: 5px; }
        .dl-select { flex: 1; background: var(--pink); color: #fff; border: none; border-radius: 6px; padding: 12px; font-size: 11px; font-weight: 900; cursor: pointer; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <!-- Login screen remains the same -->
    {% else %}
    <div class="sidebar">
        <div class="sidebar-sec">
            <button class="c-btn" style="background:var(--mint); color:#000; width:100%;" onclick="document.getElementById('vidInp').click()">LOAD VIDEO</button>
            <input type="file" id="vidInp" style="display:none" onchange="uploadVideo()">
        </div>
        <div class="sidebar-sec">
            <div class="section-title">Logos</div>
            <button class="c-btn" style="width:100%;" onclick="document.getElementById('logoInp').click()">ADD LOGOS</button>
            <input type="file" id="logoInp" style="display:none" multiple onchange="loadLogos()">
            <div id="logoBank" style="display:grid; grid-template-columns:repeat(4,1fr); gap:5px; margin-top:10px;"></div>
        </div>
        <div class="section-title" style="padding:15px 15px 0 15px;">Frame Bank</div>
        <div class="frame-bank" id="frameBank"></div>
    </div>

    <div class="workspace">
        <div id="mainGrid" class="main-grid"></div>
    </div>
    {% endif %}

    <script>
        let allFrames = [];
        let workspaceFrames = [];

        function uploadVideo() {
            const fd = new FormData();
            fd.append('video', document.getElementById('vidInp').files[0]);
            fetch('/process', { method: 'POST', body: fd }).then(r => r.json()).then(data => pollStatus(data.job_id));
        }

        function pollStatus(jid) {
            fetch(`/status/${jid}`).then(r => r.json()).then(data => {
                if (data.status === 'completed') {
                    allFrames = data.frames;
                    workspaceFrames = data.chosen_indices.map(idx => ({ url: allFrames[idx], blur: 0, sticker: false, border: false, text: "EDIT TEXT", color: "#FFFFFF" }));
                    renderAll();
                } else { setTimeout(() => pollStatus(jid), 3000); }
            });
        }

        function renderAll() {
            // Sidebar logic remains identical
            document.getElementById('frameBank').innerHTML = allFrames.map((u, i) => `
                <div class="bank-item">
                    <img src="${u}" class="bank-img">
                    <button class="icon-btn del-btn-small" onclick="deleteFromBank(${i})">X</button>
                    <button class="icon-btn add-btn" onclick="addToWorkspace(${i})">+</button>
                </div>
            `).join('');

            // Workspace Logic with Hover Zoom Container
            document.getElementById('mainGrid').innerHTML = workspaceFrames.map((f, i) => `
                <div class="editor-card">
                    <button class="card-delete" onclick="removeFromWorkspace(${i})">X</button>
                    <div class="canvas-container">
                        <div class="canvas-area" id="export-${i}" style="border: ${f.border ? '6px solid '+f.color : '0px'}">
                            <img src="${f.url}" class="bg-layer" style="filter:blur(${f.blur}px)">
                            <img src="${f.url}" class="subject-layer ${f.sticker ? 'sticker-mode' : ''}">
                            <div class="drag-item overlay-text" contenteditable="true" style="color:${f.color}">${f.text}</div>
                        </div>
                    </div>
                    <div class="card-controls">
                        <input type="color" value="${f.color}" onchange="updateCard(${i}, 'color', this.value)" style="width:100%; height:35px; border:none; background:none;">
                        <button class="c-btn" onclick="updateCard(${i}, 'sticker', !workspaceFrames[${i}].sticker)">Glow: ${f.sticker?'ON':'OFF'}</button>
                        <button class="c-btn" onclick="updateCard(${i}, 'border', !workspaceFrames[${i}].border)">Border</button>
                        <button class="c-btn" onclick="adjBlur(${i}, 5)">Blur +</button>
                        <button class="c-btn" onclick="adjBlur(${i}, -5)">Blur -</button>
                        <div class="export-box">
                            <select class="dl-select" onchange="exportFrame(${i}, this.value)">
                                <option value="">💾 EXPORT AS...</option>
                                <option value="png">PNG (Best Quality)</option>
                                <option value="jpg">JPG (Small Size)</option>
                                <option value="pdf">PDF (Print)</option>
                            </select>
                        </div>
                    </div>
                </div>
            `).join('');
            setupDraggables();
        }

        function deleteFromBank(i) { allFrames.splice(i, 1); renderAll(); }
        function removeFromWorkspace(i) { workspaceFrames.splice(i, 1); renderAll(); }
        function addToWorkspace(allIdx) {
            if(workspaceFrames.length < 6) {
                workspaceFrames.push({ url: allFrames[allIdx], blur: 0, sticker: false, border: false, text: "NEW FRAME", color: "#FFFFFF" });
                renderAll();
            }
        }

        function updateCard(i, key, val) { workspaceFrames[i][key] = val; renderAll(); }
        function adjBlur(i, val) { workspaceFrames[i].blur = Math.max(0, workspaceFrames[i].blur + val); renderAll(); }

        function exportFrame(i, format) {
            if(!format) return;
            const target = document.getElementById(`export-${i}`);
            // High-Scale (3) ensures the download isn't blurry or stretched
            html2canvas(target, { useCORS: true, scale: 3, backgroundColor: null }).then(canvas => {
                const link = document.createElement('a');
                link.download = `Viral_Studio_V55_${i}.${format}`;
                link.href = canvas.toDataURL(`image/${format === 'jpg' ? 'jpeg' : format}`);
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

        function loadLogos() {
            const files = document.getElementById('logoInp').files;
            for(let f of files) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.style.width = "100%"; img.style.cursor = "pointer";
                    img.onclick = () => addLogoToAll(e.target.result);
                    document.getElementById('logoBank').appendChild(img);
                };
                reader.readAsDataURL(f);
            }
        }

        function addLogoToAll(src) {
            document.querySelectorAll('.canvas-area').forEach(canvas => {
                const img = document.createElement('img');
                img.src = src; img.className = "drag-item"; img.style.width = "60px";
                canvas.appendChild(img);
            });
            setupDraggables();
        }
    </script>
</body>
</html>
"""

# Backend video deletion remains identical
@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    job_id = str(int(time.time())); temp_fn = f"raw_{job_id}.mp4"
    s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read', 'ContentType': 'video/mp4'})
    v_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{temp_fn}"
    handler = fal_client.submit("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
    jobs[job_id] = {'status': 'processing', 'indices': [0,5,10,15,20,25]}
    threading.Thread(target=background_monitor, args=(job_id, handler, temp_fn)).start()
    return jsonify({"job_id": job_id})

def background_monitor(jid, handler, s3_key):
    try:
        result = handler.get(); frames = [i['url'] for i in result.get('images', [])]
        s3.delete_object(Bucket=BUCKET, Key=s3_key) # PURGE S3 VIDEO
        jobs[jid]['status'] = 'completed'; jobs[jid]['frames'] = frames
    except: jobs[jid]['status'] = 'error'

# (Remaining login/status routes)
