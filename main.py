import os, boto3, fal_client, time
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- CONFIG ---
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
LAB_PASSWORD = os.environ.get("LAB_PASSWORD", "HEATHUMB2026")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "heatthumb-vault-sruli-259851212536-eu-north-1-an")

# --- UI DESIGN ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 340px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 15px; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 25px; }
        
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 18px; position: relative; }
        .img-card img { width: 100%; border-radius: 10px; display: block; background: #000; margin-bottom: 12px; }
        
        /* Logo Manager UI */
        .logo-manager { background: #000; padding: 15px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border); }
        .logo-tray { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
        .logo-item { width: 50px; height: 50px; border: 2px solid var(--border); border-radius: 6px; cursor: pointer; object-fit: contain; background: #111; }
        .logo-item.active { border-color: var(--mint); box-shadow: 0 0 10px rgba(0,255,194,0.4); }

        .lib-item { position: relative; margin-bottom: 12px; border-radius: 8px; overflow: hidden; }
        .plus-btn { position: absolute; top: 8px; right: 8px; background: var(--mint); color: #000; border: none; border-radius: 50%; width: 30px; height: 30px; font-weight: bold; cursor: pointer; z-index: 10; font-size: 20px; }

        .btn-mint { background: var(--mint); color: #000; border: none; padding: 14px; border-radius: 10px; font-weight: 900; cursor: pointer; width: 100%; text-transform: uppercase; }
        .canva-tools { display: flex; gap: 8px; margin: 12px 0; }
        .tool-btn { flex: 1; background: #2D333B; border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 6px; font-size: 10px; font-weight: bold; cursor: pointer; }
        
        .loader { position: fixed; inset: 0; background: rgba(0,0,0,0.95); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
    </style>
</head>
<body>
    <div class="loader" id="loader">
        <h2 style="color:var(--mint)">NEURAL LOGO INTEGRATION</h2>
        <p>Positioning branding elements and refining CTR...</p>
    </div>

    <div class="sidebar" id="sidebar" style="display:none;">
        <div style="padding: 20px; border-bottom: 1px solid var(--border); font-weight: 900; font-size: 11px;">RAW DISCOVERY VAULT</div>
        <div class="scroll-area" id="libraryGrid"></div>
    </div>

    <div class="workspace">
        <div id="authPanel" style="text-align:center; padding-top:100px;">
            <h1 style="font-size: 40px;">NEURAL STUDIO <span style="color:var(--mint)">V16</span></h1>
            <input type="password" id="passCode" placeholder="Access Key">
            <button onclick="checkAuth()" class="btn-mint" style="width:200px; margin-top:10px;">ENTER</button>
        </div>

        <div id="labPanel" style="display:none;">
            <div class="logo-manager">
                <div style="font-size: 12px; font-weight: bold; color: var(--blue);">MULTI-LOGO DROPZONE</div>
                <input type="file" id="logoUpload" multiple onchange="handleLogos(this)" style="margin-top:10px; font-size:11px;">
                <div id="logoTray" class="logo-tray"></div>
            </div>

            <div style="background: var(--card); border: 1px solid var(--border); padding: 20px; border-radius: 15px; margin-bottom: 25px;">
                <input type="file" id="videoFile" style="display:block; margin-bottom:15px;">
                <button onclick="processVideo()" class="btn-mint">SCAN VIDEO & CURATE BEST 6</button>
            </div>
            
            <div id="mainGrid" class="image-grid"></div>
        </div>
    </div>

    <script>
        let activeLogos = [];

        function checkAuth() { 
            if(document.getElementById('passCode').value === "{{ password }}") {
                document.getElementById('authPanel').style.display = 'none';
                document.getElementById('labPanel').style.display = 'block';
            }
        }

        function handleLogos(input) {
            Array.from(input.files).forEach(file => {
                const reader = new FileReader();
                reader.onload = e => {
                    const id = Date.now() + Math.random();
                    activeLogos.push({ id, src: e.target.result, enabled: true });
                    renderLogos();
                };
                reader.readAsDataURL(file);
            });
        }

        function renderLogos() {
            document.getElementById('logoTray').innerHTML = activeLogos.map(logo => `
                <img src="${logo.src}" class="logo-item ${logo.enabled ? 'active' : ''}" 
                     onclick="toggleLogo('${logo.id}')">
            `).join('');
        }

        function toggleLogo(id) {
            const logo = activeLogos.find(l => l.id == id);
            logo.enabled = !logo.enabled;
            renderLogos();
        }

        async function processVideo() {
            const v = document.getElementById('videoFile').files[0];
            if(!v) return alert("Select video.");
            document.getElementById('loader').style.display = 'flex';
            const fd = new FormData();
            fd.append('video', v);

            const res = await fetch('/process', { method: 'POST', body: fd });
            const data = await res.json();
            
            if(data.status === 'success') {
                document.getElementById('sidebar').style.display = 'flex';
                document.getElementById('libraryGrid').innerHTML = data.library.map(u => `
                    <div class="lib-item">
                        <img src="${u}">
                        <button class="plus-btn" onclick="promote('${u}')">+</button>
                    </div>
                `).join('');
                document.getElementById('mainGrid').innerHTML = data.pack.map(u => createCard(u)).join('');
            }
            document.getElementById('loader').style.display = 'none';
        }

        function createCard(url) {
            return `
                <div class="img-card">
                    <img src="${url}">
                    <div class="canva-tools">
                        <button class="tool-btn" onclick="quickRemix(this, 'Add thick white sticker outline around person')">GLOW</button>
                        <button class="tool-btn" onclick="quickRemix(this, 'Extremely high contrast and saturation')">POP</button>
                        <button class="tool-btn" onclick="quickRemix(this, 'Cinematic high action background')">BG SWAP</button>
                    </div>
                    <input type="text" placeholder="Headline text..." style="width:100%; background:#000; border:1px solid var(--border); color:#fff; padding:10px; border-radius:8px; box-sizing:border-box;">
                    <button class="btn-mint" style="margin-top:10px; padding:8px; font-size:11px;" onclick="remix(this)">APPLY TEXT & LOGOS</button>
                </div>`;
        }

        async function quickRemix(btn, action) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            btn.innerText = "...";
            const logosToSend = activeLogos.filter(l => l.enabled).map(l => l.src);
            
            const res = await fetch('/remix', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: img.src, prompt: action, logos: logosToSend })
            });
            const d = await res.json();
            if(d.url) img.src = d.url;
            btn.innerText = action.split(' ')[0].toUpperCase();
        }

        async function remix(btn) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            const text = card.querySelector('input').value;
            const logosToSend = activeLogos.filter(l => l.enabled).map(l => l.src);
            
            btn.innerText = "THINKING...";
            const res = await fetch('/remix', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: img.src, prompt: "Add bold headline: " + text, logos: logosToSend })
            });
            const d = await res.json();
            if(d.url) img.src = d.url;
            btn.innerText = "APPLY TEXT & LOGOS";
        }

        function promote(u) { document.getElementById('mainGrid').insertAdjacentHTML('afterbegin', createCard(u)); }
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
        
        # 1. Smarter Extraction (Skips the first 10% to avoid initial camera shake/blur)
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 25})
        raw_frames = list(dict.fromkeys([i['url'] for i in ex.get('images', [])]))

        # 2. Grab 6 frames from middle-to-end (usually where subject is most stable)
        mid = len(raw_frames) // 4
        best_6 = raw_frames[mid:mid+6] if len(raw_frames) > mid+6 else raw_frames[:6]

        s3.delete_object(Bucket=BUCKET, Key=fn)
        return jsonify({"status": "success", "pack": best_6, "library": raw_frames})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/remix', methods=['POST'])
def remix():
    d = request.json
    logo_prompt = " Place the provided logos prominently and professionally in the corners of the image." if d.get('logos') else ""
    r = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": d['url'],
        "prompt": f"{d['prompt']}.{logo_prompt} Keep original human identity perfectly.",
        "strength": 0.5
    })
    return jsonify({"url": r['images'][0]['url']})

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
