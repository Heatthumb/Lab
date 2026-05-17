import os, boto3, fal_client, time, json, threading
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "studio_v67_clean_layout"
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
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --pink: #FF007A; --red: #ff4d4d; --gold: #FFD700; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow:hidden; }
        
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; display: flex; flex-direction: column; }
        .sidebar-sec { padding: 15px; border-bottom: 1px solid var(--border); }
        .section-title { font-size: 10px; font-weight: 900; color: var(--blue); text-transform: uppercase; margin-bottom: 10px; }
        .frame-bank { padding: 10px; display: grid; grid-template-columns: 1fr; gap: 12px; }
        .bank-item { position: relative; border-radius: 6px; overflow: hidden; border: 1px solid #333; background: #000; }
        .bank-img { width: 100%; aspect-ratio: 16/9; object-fit: contain; display: block; }
        .add-btn { position: absolute; top: 5px; right: 5px; background: var(--mint); border:none; border-radius:4px; width:24px; height:24px; cursor:pointer; font-weight:900; }

        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 40px; max-width: 1400px; margin: 0 auto; }

        .editor-card { background: var(--card); border-radius: 12px; padding: 15px; border: 1px solid var(--border); position: relative; }
        
        /* Fixed Canvas: Both layers perfectly contain to prevent zooming/overlap issues */
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; overflow: hidden; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
        
        .bg-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 1; }
        .subject-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 2; pointer-events: none; }
        .sticker-mode { filter: drop-shadow(0 0 15px rgba(255,255,255,1)) drop-shadow(0 0 5px #fff); }

        .drag-item { position: absolute; cursor: move; z-index: 10; user-select: none; }
        .overlay-text { font-weight: 900; text-transform: uppercase; white-space: nowrap; padding: 5px; text-shadow: 2px 2px 12px #000; font-size: 26px; outline: none; }

        .card-controls { margin-top: 15px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .c-btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 10px; font-size: 11px; cursor: pointer; border-radius: 6px; font-weight: 700; }
        
        .ai-redraw-btn { grid-column: span 3; background: var(--gold); color: #000; font-weight: 900; border: none; padding: 12px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .ai-redraw-btn:disabled { background: #555; cursor: not-allowed; }

        /* The Export Box is BACK */
        .export-box { grid-column: span 3; display: flex; gap: 8px; margin-top: 5px; }
        .dl-select { flex: 1; background: var(--pink); color: #fff; border: none; border-radius: 6px; padding: 12px; font-size: 11px; font-weight: 900; cursor: pointer; }
        .format-select { flex: 1; background: #242b35; color: #fff; border: 1px solid var(--border); border-radius: 6px; padding: 12px; font-size: 11px; font-weight: 700; cursor: pointer; }

        #enlargeModal { position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 9999; display: none; align-items: center; justify-content: center; }
        #modalContainer { width: 85vw; height: 47.8vw; position: relative; background: #000; }
        .close-btn { position: absolute; top: -50px; right: 0; color: white; font-weight: 900; cursor: pointer; background: var(--red); padding: 10px 20px; border-radius: 6px; border:none; }
        
        .loader { width: 14px; height: 14px; border: 2px solid #000; border-bottom-color: transparent; border-radius: 50%; display: inline-block; animation: rotation 1s linear infinite; }
        @keyframes rotation { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div style="display:flex; height:100vh; width:100vw; align-items:center; justify-content:center;">
        <form method="POST" action="/login" style="background:var(--card); padding:40px; border-radius:12px; border:1px solid var(--border);">
            <h2 style="color:var(--mint); margin-top:0;">Viral Studio V67</h2>
            <input type="password" name="password" style="width:100%; padding:10px; margin-bottom:20px; border-radius:4px; border:1px solid var(--border); background:#000; color:white;">
            <button type="submit" class="c-btn" style="width:100%; background:var(--mint); color:#000;">LOGIN</button>
        </form>
    </div>
    {% else %}
    <div id="enlargeModal">
        <div id="modalContainer">
            <button class="close-btn" onclick="closeEnlarge()">EXIT PREVIEW (ESC) ✕</button>
            <div id="modalCanvas" style="width:100%; height:100%; position:relative; overflow:hidden;"></div>
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
                    workspaceFrames = [0,5,10,15,20,25].map(idx => ({ 
                        url: allFrames[idx], blur: 0, sticker: false, 
                        border: false, text: "EDIT TEXT", color: "#FFFFFF", loading: false 
                    }));
                    renderAll();
                } else { setTimeout(() => pollStatus(jid), 3000); }
            });
        }

        function renderAll() {
            document.getElementById('frameBank').innerHTML = allFrames.map((u, i) => `
                <div class="bank-item"><img src="${u}" class="bank-img"><button class="add-btn" onclick="addToWorkspace(${i})">+</button></div>`).join('');

            document.getElementById('mainGrid').innerHTML = workspaceFrames.map((f, i) => `
                <div class="editor-card">
                    <button class="card-delete" onclick="removeFromWorkspace(${i})" style="position:absolute; top:-10px; right:-10px; background:var(--red); color:white; border:none; width:28px; height:28px; border-radius:50%; font-weight:900; z-index:20; cursor:pointer;">X</button>
                    <div class="canvas-area" id="export-${i}">
                        <img src="${f.url}" class="bg-layer" style="filter:blur(${f.blur}px);">
                        <img src="${f.url}" class="subject-layer ${f.sticker ? 'sticker-mode' : ''}">
                        <div class="drag-item overlay-text" contenteditable="true" style="color:${f.color}">${f.text}</div>
                    </div>
                    <div class="card-controls">
                        <button class="ai-redraw-btn" id="btn-${i}" onclick="triggerTrueRedraw(${i})" ${f.loading ? 'disabled' : ''}>
                            ${f.loading ? '<span class="loader"></span> GENERATING OUTPAINT...' : '✨ TRUE AI REDRAW'}
                        </button>
                        <input type="color" value="${f.color}" onchange="updateCard(${i}, 'color', this.value)" style="width:100%; height:35px; border:none; background:none;">
                        <button class="c-btn" onclick="updateCard(${i}, 'sticker', !workspaceFrames[${i}].sticker)">Glow</button>
                        <button class="c-btn" style="background:var(--blue); color:#000;" onclick="openEnlarge(${i})">PREVIEW</button>
                        
                        <div class="export-box">
                            <select class="format-select" id="format-${i}">
                                <option value="16/9">YouTube (16:9)</option>
                                <option value="9/16">TikTok (9:16)</option>
                                <option value="1/1">Instagram (1:1)</option>
                            </select>
                            <button class="dl-select" onclick="exportFrame(${i})">DOWNLOAD 4K</button>
                        </div>
                    </div>
                </div>`).join('');
            setupDraggables();
        }

        async function triggerTrueRedraw(i) {
            const frame = workspaceFrames[i];
            const format = document.getElementById(`format-${i}`).value; // Read what format they want to draw for
            updateCard(i, 'loading', true);

            const res = await fetch('/redraw', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ image_url: frame.url, format: format })
            });
            const data = await res.json();
            
            if (data.redraw_url) {
                // Completely overwrite the old photo with the brand new, correctly sized AI photo
                workspaceFrames[i].url = data.redraw_url;
            }
            updateCard(i, 'loading', false);
        }

        function exportFrame(i) {
            const target = document.getElementById(`export-${i}`);
            const format = document.getElementById(`format-${i}`).value;
            let finalW = 3840, finalH = 2160; 
            if (format === "9/16") { finalW = 2160; finalH = 3840; }
            else if (format === "1/1") { finalW = 2160; finalH = 2160; }

            const offscreen = target.cloneNode(true);
            offscreen.style.width = finalW + "px"; offscreen.style.height = finalH + "px";
            offscreen.style.position = "fixed"; offscreen.style.top = "-9999px";
            document.body.appendChild(offscreen);

            html2canvas(offscreen, { useCORS: true, scale: 1, backgroundColor: "#000", width: finalW, height: finalH }).then(canvas => {
                const link = document.createElement('a');
                link.download = `ViralStudio_Outpaint_${format.replace('/','x')}.png`;
                link.href = canvas.toDataURL("image/png", 1.0);
                link.click();
                document.body.removeChild(offscreen);
            });
        }

        function openEnlarge(i) {
            const original = document.getElementById(`export-${i}`);
            const modalCanvas = document.getElementById('modalCanvas');
            modalCanvas.innerHTML = original.innerHTML; 
            document.getElementById('enlargeModal').style.display = 'flex';
        }

        function closeEnlarge() { document.getElementById('enlargeModal').style.display = 'none'; }
        function removeFromWorkspace(i) { workspaceFrames.splice(i, 1); renderAll(); }
        function addToWorkspace(allIdx) { 
            workspaceFrames.push({ url: allFrames[allIdx], blur: 0, sticker: false, border: false, text: "NEW FRAME", color: "#FFFFFF", loading: false }); 
            renderAll(); 
        }
        function updateCard(i, key, val) { workspaceFrames[i][key] = val; renderAll(); }
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
                    img.onclick = () => {
                        document.querySelectorAll('.canvas-area').forEach(c => {
                            const clone = img.cloneNode(); clone.className = "drag-item";
                            c.appendChild(clone);
                        }); setupDraggables();
                    };
                    document.getElementById('logoBank').appendChild(img);
                }; reader.readAsDataURL(f);
            }
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

@app.route('/redraw', methods=['POST'])
def redraw():
    img_url = request.json.get('image_url')
    format_ratio = request.json.get('format', '16/9')
    
    # Tell the AI exactly what shape it needs to draw
    prompt_map = {
        "16/9": "expand the background to 16:9 cinematic landscape ratio",
        "9/16": "expand the background to 9:16 vertical ratio",
        "1/1": "expand the background to 1:1 square ratio"
    }
    
    prompt = prompt_map.get(format_ratio, "expand the background")

    result = fal_client.subscribe("fal-ai/flux-pro/v1/fill", {
        "image_url": img_url,
        "prompt": f"{prompt}, keeping the central subject pristine and matching colors seamlessly",
        "expand_direction": "both"
    })
    return jsonify({"redraw_url": result['images'][0]['url']})

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
