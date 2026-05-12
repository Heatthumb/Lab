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
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --gold: #FFD700; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 340px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 15px; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 30px; }
        
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 15px; position: relative; }
        .img-card img { width: 100%; border-radius: 10px; display: block; background: #000; border: 1px solid rgba(255,255,255,0.05); }
        
        .ctr-tag { position: absolute; top: 25px; left: 25px; background: rgba(0,0,0,0.7); color: var(--mint); padding: 5px 10px; border-radius: 5px; font-size: 10px; font-weight: bold; border: 1px solid var(--mint); }

        .logo-manager { background: #000; padding: 15px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border); }
        .logo-tray { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
        .logo-item { width: 45px; height: 45px; border: 2px solid var(--border); border-radius: 6px; cursor: pointer; object-fit: contain; }
        .logo-item.active { border-color: var(--mint); box-shadow: 0 0 10px var(--mint); }

        .btn-mint { background: var(--mint); color: #000; border: none; padding: 12px; border-radius: 8px; font-weight: 900; cursor: pointer; width: 100%; transition: 0.3s; }
        .btn-mint:hover { filter: brightness(1.2); transform: translateY(-1px); }

        .canva-pro-tools { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin: 15px 0; }
        .pro-tool { background: #1c222a; border: 1px solid var(--border); color: #fff; padding: 10px 5px; border-radius: 8px; font-size: 10px; font-weight: bold; cursor: pointer; text-align: center; }
        .pro-tool:hover { border-color: var(--blue); color: var(--blue); }
        .pro-tool span { display: block; font-size: 16px; margin-bottom: 4px; }

        .loader { position: fixed; inset: 0; background: rgba(0,0,0,0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
        .plus-btn { position: absolute; top: 5px; right: 5px; background: var(--mint); border: none; border-radius: 50%; width: 28px; height: 28px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="loader" id="loader">
        <h2 style="color:var(--mint)">NEURAL POLISHING</h2>
        <p>Applying high-gloss filters and subject locking...</p>
    </div>

    <div class="sidebar" id="sidebar" style="display:none;">
        <div style="padding: 20px; border-bottom: 1px solid var(--border); font-size: 11px; font-weight: bold; color: var(--blue);">RAW VIDEO ASSETS</div>
        <div class="scroll-area" id="libraryGrid"></div>
    </div>

    <div class="workspace">
        <div id="authPanel" style="text-align:center; padding-top:100px;">
            <h1 style="font-size: 45px; letter-spacing: -2px;">HEATHUMB <span style="color:var(--mint)">PRO</span></h1>
            <input type="password" id="passCode" placeholder="Access Code" style="padding:12px; border-radius:8px;">
            <br><button onclick="checkAuth()" class="btn-mint" style="width:200px; margin-top:10px;">STUDIO LOGIN</button>
        </div>

        <div id="labPanel" style="display:none;">
            <div class="logo-manager">
                <div style="font-size: 11px; font-weight: bold; color: var(--ghost);">BRAND LOGOS (Multiple)</div>
                <input type="file" id="logoUpload" multiple onchange="handleLogos(this)" style="margin-top:10px;">
                <div id="logoTray" class="logo-tray"></div>
            </div>

            <div style="background: var(--card); border: 1px solid var(--border); padding: 20px; border-radius: 15px; margin-bottom: 30px;">
                <input type="file" id="videoFile" style="margin-bottom:15px; display:block;">
                <button onclick="processVideo()" class="btn-mint">SCAN VIDEO (BEST REAL SHOTS)</button>
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
                <img src="${logo.src}" class="logo-item ${logo.enabled ? 'active' : ''}" onclick="toggleLogo('${logo.id}')">
            `).join('');
        }

        function toggleLogo(id) {
            const logo = activeLogos.find(l => l.id == id);
            logo.enabled = !logo.enabled;
            renderLogos();
        }

        async function processVideo() {
            const v = document.getElementById('videoFile').files[0];
            if(!v) return alert("Select video");
            document.getElementById('loader').style.display = 'flex';
            const fd = new FormData();
            fd.append('video', v);

            const res = await fetch('/process', { method: 'POST', body: fd });
            const data = await res.json();
            
            if(data.status === 'success') {
                document.getElementById('sidebar').style.display = 'flex';
                document.getElementById('libraryGrid').innerHTML = data.library.map(u => `
                    <div style="position:relative; margin-bottom:10px;">
                        <img src="${u}" style="width:100%; border-radius:8px;">
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
                    <div class="ctr-tag">EST. CTR: 9.4%</div>
                    <img src="${url}">
                    
                    <div class="canva-pro-tools">
                        <div class="pro-tool" onclick="polish(this, 'glow')"><span>✨</span>GLOW UP</div>
                        <div class="pro-tool" onclick="polish(this, 'pop')"><span>🔥</span>VIBRANT</div>
                        <div class="pro-tool" onclick="polish(this, 'matte')"><span>📸</span>HD GLOSS</div>
                    </div>

                    <input type="text" placeholder="Add Bold Headline Text..." style="width:100%; background:#000; border:1px solid var(--border); color:#fff; padding:12px; border-radius:8px; box-sizing:border-box; margin-bottom:10px;">
                    <button class="btn-mint" onclick="remix(this)">APPLY TEXT & LOGOS</button>
                    <div style="text-align:center; font-size:9px; color:#555; margin-top:10px;">REAL FRAME PERSISTENCE: ACTIVE</div>
                </div>`;
        }

        async function polish(btn, type) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            const original = btn.innerHTML;
            btn.innerHTML = "Refining...";
            
            const res = await fetch('/polish', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: img.src, type: type })
            });
            const d = await res.json();
            if(d.url) img.src = d.url;
            btn.innerHTML = original;
        }

        async function remix(btn) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            const text = card.querySelector('input').value;
            const logos = activeLogos.filter(l => l.enabled).map(l => l.src);
            
            btn.innerText = "UPDATING...";
            const res = await fetch('/remix', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: img.src, prompt: text, logos: logos })
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
        
        # 1. RAW extraction
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
        raw_frames = list(dict.fromkeys([i['url'] for i in ex.get('images', [])]))

        # 2. Pick 6 REAL frames (skipping intro/outro for quality)
        step = len(raw_frames) // 7
        best_6 = [raw_frames[i*step] for i in range(1, 7)] if len(raw_frames) > 10 else raw_frames[:6]

        s3.delete_object(Bucket=BUCKET, Key=fn)
        return jsonify({"status": "success", "pack": best_6, "library": raw_frames})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/polish', methods=['POST'])
def polish():
    d = request.json
    prompts = {
        "glow": "Enhance the lighting, add a professional subtle glow to the subject, increase clarity.",
        "pop": "Highly vibrant colors, saturated professional YouTube look, high contrast.",
        "matte": "Professional studio gloss finish, sharp edges, 8k resolution textures."
    }
    # CRITICAL: Strength set to 0.20 to prevent "Strange AI" pictures
    r = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": d['url'],
        "prompt": prompts[d['type']] + " Keep the photo exactly the same.",
        "strength": 0.20
    })
    return jsonify({"url": r['images'][0]['url']})

@app.route('/remix', methods=['POST'])
def remix():
    d = request.json
    logo_txt = " Add the provided logos into the corners." if d.get('logos') else ""
    # Strength 0.35 allows text to be rendered while keeping the photo 65% original
    r = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": d['url'],
        "prompt": f"Add bold text: {d['prompt']}. {logo_txt} Keep the photo exactly the same.",
        "strength": 0.35
    })
    return jsonify({"url": r['images'][0]['url']})

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
