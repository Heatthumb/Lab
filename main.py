import os, boto3, fal_client, time, json, threading, random
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "studio_v61_adaptive"
ACCESS_PASSWORD = "Heathumb2026"

# Cloud & S3 Logic (As per instructions: video deleted after extraction)
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
        
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; display: flex; flex-direction: column; }
        .sidebar-sec { padding: 15px; border-bottom: 1px solid var(--border); }
        .section-title { font-size: 10px; font-weight: 900; color: var(--blue); text-transform: uppercase; margin-bottom: 10px; }
        .frame-bank { padding: 10px; display: grid; grid-template-columns: 1fr; gap: 12px; }
        .bank-item { position: relative; border-radius: 6px; overflow: hidden; border: 1px solid #333; background: #000; }
        .bank-img { width: 100%; object-fit: contain; display: block; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 40px; max-width: 1400px; margin: 0 auto; }

        .editor-card { background: var(--card); border-radius: 12px; padding: 15px; border: 1px solid var(--border); position: relative; }
        
        /* ADAPTIVE CANVAS: Removes fixed 16/9 to allow phone videos to be tall */
        .canvas-area { position: relative; width: 100%; background: #000; overflow: hidden; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
        .canvas-landscape { aspect-ratio: 16/9; }
        .canvas-portrait { aspect-ratio: 9/16; max-height: 70vh; margin: 0 auto; }
        
        .bg-layer { position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 1; }
        .subject-layer { position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 2; pointer-events: none; }
        .sticker-mode { filter: drop-shadow(0 0 15px rgba(255,255,255,1)) drop-shadow(0 0 5px #fff); }

        .drag-item { position: absolute; cursor: move; z-index: 10; user-select: none; }
        .overlay-text { font-weight: 900; text-transform: uppercase; white-space: nowrap; padding: 5px; text-shadow: 2px 2px 12px #000; font-size: 26px; outline: none; }

        .card-controls { margin-top: 15px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .c-btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 10px; font-size: 11px; cursor: pointer; border-radius: 6px; font-weight: 700; }
        .dl-select { grid-column: span 3; background: var(--pink); color: #fff; border: none; border-radius: 6px; padding: 12px; font-size: 11px; font-weight: 900; cursor: pointer; }

        #enlargeModal { position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 9999; display: none; align-items: center; justify-content: center; }
        #modalContainer { position: relative; background: #000; border: 1px solid #333; display: flex; align-items: center; justify-content: center; }
        .close-btn { position: absolute; top: -50px; right: 0; color: white; font-weight: 900; cursor: pointer; background: var(--red); padding: 8px 20px; border-radius: 4px; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div style="display:flex; height:100vh; width:100vw; align-items:center; justify-content:center;">
        <form method="POST" action="/login" style="background:var(--card); padding:40px; border-radius:12px; border:1px solid var(--border);">
            <h2 style="color:var(--mint); margin-top:0;">Viral Studio V61</h2>
            <input type="password" name="password" style="width:100%; padding:10px; margin-bottom:20px; border-radius:4px; border:1px solid var(--border); background:#000; color:white;">
            <button type="submit" class="c-btn" style="width:100%; background:var(--mint); color:#000;">LOGIN</button>
        </form>
    </div>
    {% else %}
    <div id="enlargeModal" onclick="closeEnlarge()">
        <div id="modalContainer" onclick="event.stopPropagation()">
            <div class="close-btn" onclick="closeEnlarge()">✕ CLOSE (ESC)</div>
            <div id="modalCanvas" style="position:relative; overflow:hidden;"></div>
        </div>
    </div>

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
    <div class="workspace"><div id="mainGrid" class="main-grid"></div></div>
    {% endif %}

    <script>
        let allFrames = []; let workspaceFrames = [];
        document.addEventListener('keydown', (e) => { if(e.key === "Escape") closeEnlarge(); });

        function uploadVideo() {
            const fd = new FormData(); fd.append('video', document.getElementById('vidInp').files[0]);
            fetch('/process', { method: 'POST', body: fd }).then(r => r.json()).then(data => pollStatus(data.job_id));
        }

        function pollStatus(jid) {
            fetch(`/status/${jid}`).then(r => r.json()).then(data => {
                if (data.status === 'completed') {
                    allFrames = data.frames;
                    detectAndRender();
                } else { setTimeout(() => pollStatus(jid), 3000); }
            });
        }

        function detectAndRender() {
            const img = new Image();
            img.src = allFrames[0];
            img.onload = function() {
                const isPortrait = img.height > img.width;
                workspaceFrames = [0,5,10,15,20,25].map(idx => ({ 
                    url: allFrames[idx], blur: 0, sticker: false, border: false, 
                    text: "EDIT TEXT", color: "#FFFFFF", portrait: isPortrait 
                }));
                renderAll();
            };
        }

        function renderAll() {
            document.getElementById('frameBank').innerHTML = allFrames.map((u, i) => `
                <div class="bank-item"><img src="${u}" class="bank-img"><button class="icon-btn add-btn" onclick="addToWorkspace(${i})">+</button></div>`).join('');

            document.getElementById('mainGrid').innerHTML = workspaceFrames.map((f, i) => `
                <div class="editor-card">
                    <div class="canvas-area ${f.portrait ? 'canvas-portrait' : 'canvas-landscape'}" id="export-${i}" style="border: ${f.border ? '6px solid '+f.color : '0px'}">
                        <img src="${f.url}" class="bg-layer" style="filter:blur(${f.blur}px)">
                        <img src="${f.url}" class="subject-layer ${f.sticker ? 'sticker-mode' : ''}">
                        <div class="drag-item overlay-text" contenteditable="true" style="color:${f.color}">${f.text}</div>
                    </div>
                    <div class="card-controls">
                        <input type="color" value="${f.color}" onchange="updateCard(${i}, 'color', this.value)" style="width:100%; height:35px; border:none; background:none;">
                        <button class="c-btn" onclick="updateCard(${i}, 'sticker', !workspaceFrames[${i}].sticker)">Glow</button>
                        <button class="c-btn" onclick="adjBlur(${i}, 5)">Blur +</button>
                        <button class="c-btn" style="background:var(--blue); color:#000;" onclick="openEnlarge(${i})">PREVIEW</button>
                        <button class="dl-select" onclick="exportFrame(${i})">DOWNLOAD HD (NO STRETCH)</button>
                    </div>
                </div>`).join('');
            setupDraggables();
        }

        function openEnlarge(i) {
            const f = workspaceFrames[i];
            const original = document.getElementById(`export-${i}`);
            const modalContainer = document.getElementById('modalContainer');
            const modalCanvas = document.getElementById('modalCanvas');
            
            modalCanvas.innerHTML = original.innerHTML;
            modalCanvas.className = f.portrait ? 'canvas-portrait' : 'canvas-landscape';
            modalCanvas.style.width = f.portrait ? "30vw" : "85vw";
            
            document.getElementById('enlargeModal').style.display = 'flex';
        }

        function closeEnlarge() { document.getElementById('enlargeModal').style.display = 'none'; }
        
        function exportFrame(i) {
            const target = document.getElementById(`export-${i}`);
            const f = workspaceFrames[i];
            
            // AI Detection for output size
            const exportW = f.portrait ? 1080 : 1920;
            const exportH = f.portrait ? 1920 : 1080;

            html2canvas(target, { 
                useCORS: true, 
                scale: 2, 
                backgroundColor: "#000",
                width: target.offsetWidth,
                height: target.offsetHeight
            }).then(canvas => {
                const link = document.createElement('a');
                link.download = `Viral_Studio_HD_${i}.png`;
                link.href = canvas.toDataURL("image/png");
                link.click();
            });
        }

        function addToWorkspace(allIdx) {
            const img = new Image(); img.src = allFrames[allIdx];
            img.onload = () => {
                workspaceFrames.push({ url: allFrames[allIdx], blur: 0, sticker: false, border: false, text: "NEW", color: "#FFFFFF", portrait: img.height > img.width });
                renderAll();
            };
        }

        function updateCard(i, key, val) { workspaceFrames[i][key] = val; renderAll(); }
        function adjBlur(i, val) { workspaceFrames[i].blur = Math.max(0, workspaceFrames[i].blur + val); renderAll(); }
        function setupDraggables() {
            document.querySelectorAll('.drag-item').forEach(el => {
                el.onmousedown = function(e) {
                    let ox = e.clientX - el.offsetLeft; let oy = e.clientY - el.offsetTop;
                    document.onmousemove = function(e) { el.style.left = (e.clientX - ox) + 'px'; el.style.top = (e.clientY - oy) + 'px'; }
                    document.onmouseup = () => document.onmousemove = null;
                }
            });
        }
        function loadLogos() {
            const files = document.getElementById('logoInp').files;
            for(let f of files) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const img = document.createElement('img'); img.src = e.target.result;
                    img.style.width = "60px"; img.className = "drag-item";
                    img.onclick = () => addLogoToAll(e.target.result);
                    document.getElementById('logoBank').appendChild(img);
                }; reader.readAsDataURL(f);
            }
        }
        function addLogoToAll(src) {
            document.querySelectorAll('.canvas-area').forEach(canvas => {
                const img = document.createElement('img'); img.src = src; img.className = "drag-item"; img.style.width = "60px";
                canvas.appendChild(img);
            }); setupDraggables();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD: session['logged_in'] = True
    return redirect(url_for('home'))

@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    job_id = str(int(time.time())); temp_fn = f"raw_{job_id}.mp4"
    s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read', 'ContentType': 'video/mp4'})
    v_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{temp_fn}"
    handler = fal_client.submit("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
    jobs[job_id] = {'status': 'processing'}
    threading.Thread(target=background_monitor, args=(job_id, handler, temp_fn)).start()
    return jsonify({"job_id": job_id})

def background_monitor(jid, handler, s3_key):
    try:
        result = handler.get(); frames = [i['url'] for i in result.get('images', [])]
        s3.delete_object(Bucket=BUCKET, Key=s3_key) 
        jobs[jid]['status'] = 'completed'; jobs[jid]['frames'] = frames
    except: jobs[jid]['status'] = 'error'

@app.route('/status/<job_id>')
def status(job_id):
    job = jobs.get(job_id, {'status': 'not_found'})
    return jsonify({'status': job['status'], 'frames': job.get('frames', [])})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
