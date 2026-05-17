import os, boto3, fal_client, time, threading
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "studio_v80_raw_clarity"
ACCESS_PASSWORD = "Heathumb2026"

# Cloud Config
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
        
        /* SHARPNESS FIX: Anti-aliasing and crisp rendering for faces */
        .bank-img { 
            width: 100%; aspect-ratio: 16/9; object-fit: contain; display: block; 
            image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;
        }
        
        .add-btn { position: absolute; top: 5px; right: 5px; background: var(--mint); border:none; border-radius:4px; width:24px; height:24px; cursor:pointer; font-weight:900; }

        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 40px; max-width: 1400px; margin: 0 auto; }
        .editor-card { background: var(--card); border-radius: 12px; padding: 15px; border: 1px solid var(--border); position: relative; }
        
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; overflow: hidden; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
        
        /* SUBJECT CLARITY: Using contrast and brightness filters instead of AI upscaling */
        .bg-layer { 
            position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 1; 
            filter: contrast(1.05) brightness(1.02);
            image-rendering: high-quality;
        }
        
        .drag-item { position: absolute; cursor: move; z-index: 10; user-select: none; font-weight: 900; text-transform: uppercase; text-shadow: 2px 2px 15px #000; font-size: 28px; outline: none; padding: 5px; }
        .text-placeholder { color: var(--gold); border: 2px dashed var(--gold); }

        .card-controls { margin-top: 15px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .c-btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 10px; font-size: 11px; cursor: pointer; border-radius: 6px; font-weight: 700; }
        
        .ai-redraw-btn { grid-column: span 3; background: var(--gold); color: #000; font-weight: 900; border: none; padding: 12px; border-radius: 6px; cursor: pointer; }
        .ai-redraw-btn:disabled { background: #444; color: #888; cursor: wait; }

        .export-box { grid-column: span 3; display: flex; gap: 8px; margin-top: 5px; }
        .dl-select { flex: 1; background: var(--pink); color: #fff; border: none; border-radius: 6px; padding: 12px; font-size: 11px; font-weight: 900; cursor: pointer; }
        .format-select { flex: 1; background: #242b35; color: #fff; border: 1px solid var(--border); border-radius: 6px; padding: 12px; font-size: 11px; font-weight: 700; }

        /* ULTRA PREVIEW: Max resolution container */
        #enlargeModal { position: fixed; inset: 0; background: rgba(0,0,0,0.98); z-index: 9999; display: none; align-items: center; justify-content: center; }
        #modalContainer { width: 90vw; height: 50.6vw; position: relative; background: #000; border: 1px solid #444; border-radius: 4px; overflow: hidden; }
        .close-btn { position: absolute; top: 20px; right: 20px; color: white; font-weight: 900; cursor: pointer; background: var(--red); padding: 10px 20px; border-radius: 6px; border:none; z-index:10001; }
        
        .loader { width: 12px; height: 12px; border: 2px solid #000; border-bottom-color: transparent; border-radius: 50%; display: inline-block; animation: rotation 1s linear infinite; margin-right: 8px; }
        @keyframes rotation { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div style="display:flex; height:100vh; width:100vw; align-items:center; justify-content:center;">
        <form method="POST" action="/login" style="background:var(--card); padding:40px; border-radius:12px; border:1px solid var(--border);">
            <h2 style="color:var(--mint); margin-top:0;">Viral Studio V80</h2>
            <input type="password" name="password" style="width:100%; padding:10px; margin-bottom:20px; border-radius:4px; border:1px solid var(--border); background:#000; color:white;">
            <button type="submit" class="c-btn" style="width:100%; background:var(--mint); color:#000;">LOGIN</button>
        </form>
    </div>
    {% else %}
    <div id="enlargeModal">
        <div id="modalContainer">
            <button class="close-btn" onclick="closeEnlarge()">✕ CLOSE</button>
            <div id="modalCanvas" style="width:100%; height:100%; position:relative;"></div>
        </div>
    </div>

    <div class="sidebar">
        <div class="sidebar-sec">
            <button class="c-btn" style="background:var(--mint); color:#000; width:100%;" onclick="document.getElementById('vidInp').click()">LOAD VIDEO SOURCE</button>
            <input type="file" id="vidInp" style="display:none" onchange="uploadVideo()">
        </div>
        <div class="section-title" style="padding:15px;">Ultra-Sharp Bank</div>
        <div class="frame-bank" id="frameBank"></div>
    </div>

    <div class="workspace">
        <div id="mainGrid" class="main-grid"></div>
    </div>
    {% endif %}

    <script>
        let allFrames = []; let workspaceFrames = [];
        let selectedText = null;

        function uploadVideo() {
            const fd = new FormData(); fd.append('video', document.getElementById('vidInp').files[0]);
            fetch('/process', { method: 'POST', body: fd }).then(r => r.json()).then(data => pollStatus(data.job_id));
        }

        function pollStatus(jid) {
            fetch(`/status/${jid}`).then(r => r.json()).then(data => {
                if (data.status === 'completed') {
                    allFrames = data.frames;
                    workspaceFrames = [0,5,10,15,20,25].map(idx => ({ 
                        url: allFrames[idx], blur: 0, textElements: [], status: 'idle', errorMsg: "" 
                    }));
                    renderAll();
                } else { setTimeout(() => pollStatus(jid), 2000); }
            });
        }

        function renderAll() {
            if (!document.getElementById('mainGrid')) return;
            document.getElementById('frameBank').innerHTML = allFrames.map((u, i) => `
                <div class="bank-item"><img src="${u}" class="bank-img"><button class="add-btn" onclick="addToWorkspace(${i})">+</button></div>`).join('');

            document.getElementById('mainGrid').innerHTML = workspaceFrames.map((f, i) => `
                <div class="editor-card">
                    <button onclick="removeFromWorkspace(${i})" style="position:absolute; top:-10px; right:-10px; border-radius:50%; border:none; background:red; color:white; width:24px; height:24px; cursor:pointer; font-weight:bold; z-index:20;">X</button>
                    <div class="canvas-area" id="export-${i}">
                        <img src="${f.url}" class="bg-layer" style="filter:blur(${f.blur}px) contrast(1.05) brightness(1.02);">
                        ${f.textElements.map((t, ti) => `
                            <div class="drag-item ${t.isPlaceholder ? 'text-placeholder' : ''}" 
                                 id="text-${i}-${ti}"
                                 contenteditable="true" 
                                 style="color:${t.color}; top:${t.top}px; left:${t.left}px;"
                                 onfocus="selectedText={cardIdx:${i}, textIdx:${ti}}; if('${t.text}'==='TYPE HERE'){this.innerText=''; this.classList.remove('text-placeholder');}"
                                 onblur="workspaceFrames[${i}].textElements[${ti}].text=this.innerText">
                                ${t.text}
                            </div>
                        `).join('')}
                    </div>
                    <div class="card-controls">
                        <button class="ai-redraw-btn" onclick="triggerRedraw(${i})" ${f.status === 'loading' ? 'disabled' : ''}>
                            ${f.status === 'loading' ? '<span class="loader"></span> ANALYZING...' : '✨ AI EXPANSION (4K)'}
                        </button>
                        
                        <button class="c-btn" style="background:var(--mint); color:#000;" onclick="addText(${i})">+ TEXT</button>
                        <button class="c-btn" style="background:var(--red);" onclick="delText(${i})">❌ DELETE</button>
                        <button class="c-btn" style="background:var(--blue); color:#000;" onclick="openEnlarge(${i})">PREVIEW</button>
                        
                        <div class="export-box">
                            <select class="format-select" id="format-${i}">
                                <option value="16/9">YouTube (16:9)</option>
                                <option value="9/16">TikTok (9:16)</option>
                            </select>
                            <button class="dl-select" onclick="exportFrame(${i})">DOWNLOAD</button>
                        </div>
                    </div>
                </div>`).join('');
            setupDraggables();
        }

        function addText(i) {
            workspaceFrames[i].textElements.push({ text: "TYPE HERE", color: "#FFFFFF", top: 50, left: 50, isPlaceholder: true });
            renderAll();
        }

        function delText(i) {
            if (selectedText && selectedText.cardIdx === i) {
                workspaceFrames[i].textElements.splice(selectedText.textIdx, 1);
                selectedText = null;
                renderAll();
            } else if (workspaceFrames[i].textElements.length > 0) {
                workspaceFrames[i].textElements.pop();
                renderAll();
            }
        }

        async function triggerRedraw(i) {
            const format = document.getElementById(`format-${i}`).value;
            workspaceFrames[i].status = 'loading'; renderAll();
            try {
                const res = await fetch('/redraw', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ image_url: workspaceFrames[i].url, format: format })
                });
                const data = await res.json();
                if (data.redraw_url) { workspaceFrames[i].url = data.redraw_url; workspaceFrames[i].status = 'idle'; }
            } catch (e) { workspaceFrames[i].status = 'idle'; }
            renderAll();
        }

        function exportFrame(i) {
            const target = document.getElementById(`export-${i}`);
            html2canvas(target, { useCORS: true, scale: 4, logging: false }).then(canvas => {
                const link = document.createElement('a');
                link.download = `Variant_HighRes.png`;
                link.href = canvas.toDataURL("image/png");
                link.click();
            });
        }

        function openEnlarge(i) {
            document.getElementById('modalCanvas').innerHTML = document.getElementById(`export-${i}`).innerHTML;
            document.getElementById('enlargeModal').style.display = 'flex';
        }

        function closeEnlarge() { document.getElementById('enlargeModal').style.display = 'none'; }
        function removeFromWorkspace(i) { workspaceFrames.splice(i, 1); renderAll(); }
        function addToWorkspace(allIdx) { workspaceFrames.push({ url: allFrames[allIdx], blur: 0, textElements: [], status: 'idle', errorMsg: "" }); renderAll(); }

        function setupDraggables() {
            document.querySelectorAll('.drag-item').forEach(el => {
                el.onmousedown = function(e) {
                    let ox = e.clientX - el.offsetLeft; let oy = e.clientY - el.offsetTop;
                    const cIdx = el.id.split('-')[1]; const tIdx = el.id.split('-')[2];
                    document.onmousemove = function(e) { 
                        el.style.left = (e.clientX - ox) + 'px'; el.style.top = (e.clientY - oy) + 'px'; 
                        workspaceFrames[cIdx].textElements[tIdx].left = el.offsetLeft;
                        workspaceFrames[cIdx].textElements[tIdx].top = el.offsetTop;
                    }
                    document.onmouseup = () => document.onmousemove = null;
                }
            });
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
    job_id = str(int(time.time())); temp_fn = f"src_{job_id}.mp4"
    s3.upload_fileobj(video, BUCKET, temp_fn, ExtraArgs={'ACL': 'public-read'})
    v_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{temp_fn}"
    
    # TECHNOLOGY UPGRADE: Using 'png' as the raw extraction format to preserve subject detail
    handler = fal_client.submit("fal-ai/workflow-utilities/extract-nth-frame", {
        "video_url": v_url, 
        "max_frames": 30,
        "format": "png" 
    })
    jobs[job_id] = {'status': 'processing'}
    threading.Thread(target=background_monitor, args=(job_id, handler, temp_fn)).start()
    return jsonify({"job_id": job_id})

@app.route('/redraw', methods=['POST'])
def redraw():
    img_url = request.json.get('image_url')
    fmt = request.json.get('format', '16/9')
    side_p = 512 if fmt != "9/16" else 0
    top_p = 512 if fmt == "9/16" else 0
    try:
        # Png output for expansion maintains facial sharpness
        result = fal_client.subscribe("fal-ai/image-apps-v2/outpaint", {
            "image_url": img_url,
            "left_padding": side_p, "right_padding": side_p,
            "top_padding": top_p, "bottom_padding": top_p,
            "prompt": "Vivid cinematic professional background studio lighting.",
            "enable_safety_checker": False,
            "output_format": "png"
        })
        return jsonify({"redraw_url": result['images'][0]['url']})
    except Exception as e: return jsonify({"error": str(e)}), 500

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
