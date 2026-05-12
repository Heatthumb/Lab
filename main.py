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
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --red: #FF4B4B; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 30px; }

        /* Logo Manager */
        .logo-section { padding: 15px; border-bottom: 1px solid var(--border); background: #11151b; }
        .logo-list { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
        .logo-wrap { position: relative; width: 50px; height: 50px; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
        .logo-wrap img { width: 100%; height: 100%; object-fit: contain; background: #000; }
        .logo-del { position: absolute; top: 0; right: 0; background: var(--red); color: white; border: none; font-size: 8px; cursor: pointer; padding: 2px 4px; }

        /* Card Styling */
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 18px; position: relative; }
        .frame-container { position: relative; width: 100%; border-radius: 10px; overflow: hidden; border: 4px solid transparent; transition: 0.2s; }
        .frame-container img { width: 100%; display: block; }
        
        /* Layer Overlays */
        .manual-text { 
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 90%; text-align: center; color: white; font-weight: 900; 
            text-transform: uppercase; line-height: 1; pointer-events: none;
            text-shadow: 3px 3px 0 #000, -2px -2px 0 #000; font-size: 28px; display: none;
        }
        .applied-logo { position: absolute; bottom: 10px; right: 10px; width: 60px; pointer-events: none; opacity: 0.9; display: none; }

        .tools { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 15px 0; }
        .tool-btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 10px 2px; border-radius: 8px; font-size: 10px; cursor: pointer; font-weight: bold; }
        .tool-btn.active { background: var(--blue); color: #000; }

        .btn-mint { background: var(--mint); color: #000; border: none; padding: 15px; border-radius: 10px; font-weight: 900; cursor: pointer; width: 100%; }
        .loader { position: fixed; inset: 0; background: rgba(0,0,0,0.95); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
        
        .side-plus { position: absolute; top: 8px; right: 8px; background: var(--mint); color: #000; border: none; border-radius: 50%; width: 30px; height: 30px; font-weight: 900; cursor: pointer; }
    </style>
</head>
<body>
    <div class="loader" id="loader"><h2>CURATING BEST 6</h2></div>

    <div class="sidebar" id="sidebar" style="display:none;">
        <div class="logo-section">
            <span style="font-size: 10px; font-weight: bold; color: var(--blue);">BRANDING LOGOS</span>
            <input type="file" id="logoInp" multiple onchange="uploadLogos(this)" style="display:none;">
            <button onclick="document.getElementById('logoInp').click()" style="width:100%; margin-top:5px; font-size:9px; cursor:pointer;">+ ADD LOGOS</button>
            <div id="logoList" class="logo-list"></div>
        </div>
        <div id="libraryGrid" style="padding: 15px; overflow-y: auto; flex: 1;"></div>
    </div>

    <div class="workspace">
        <div id="uploadZone" style="background: var(--card); border: 2px dashed var(--border); padding: 40px; border-radius: 20px; text-align: center; margin-bottom: 30px;">
            <input type="file" id="videoFile" style="margin-bottom: 20px;">
            <button onclick="processVideo()" class="btn-mint">SCAN & EXTRACT SHARP FRAMES</button>
        </div>
        <div id="mainGrid" class="image-grid"></div>
    </div>

    <script>
        let currentLogos = [];

        function uploadLogos(input) {
            Array.from(input.files).forEach(file => {
                const reader = new FileReader();
                reader.onload = e => {
                    const id = Date.now() + Math.random();
                    currentLogos.push({ id, src: e.target.result });
                    renderLogos();
                };
                reader.readAsDataURL(file);
            });
        }

        function renderLogos() {
            document.getElementById('logoList').innerHTML = currentLogos.map(l => `
                <div class="logo-wrap">
                    <img src="${l.src}" onclick="applyLogoToAll('${l.src}')" style="cursor:pointer" title="Click to apply to all workspace frames">
                    <button class="logo-del" onclick="deleteLogo('${l.id}')">X</button>
                </div>
            `).join('');
        }

        function deleteLogo(id) {
            currentLogos = currentLogos.filter(l => l.id != id);
            renderLogos();
        }

        function applyLogoToAll(src) {
            document.querySelectorAll('.applied-logo').forEach(img => {
                img.src = src;
                img.style.display = 'block';
            });
        }

        async function processVideo() {
            const v = document.getElementById('videoFile').files[0];
            if(!v) return;
            document.getElementById('loader').style.display = 'flex';
            const fd = new FormData();
            fd.append('video', v);

            const res = await fetch('/process', { method: 'POST', body: fd });
            const data = await res.json();
            
            if(data.status === 'success') {
                document.getElementById('sidebar').style.display = 'flex';
                document.getElementById('libraryGrid').innerHTML = data.library.map(u => `
                    <div style="position:relative; margin-bottom:10px;">
                        <img src="${u}" style="width:100%; border-radius:6px;">
                        <button class="side-plus" onclick="promote('${u}')">+</button>
                    </div>
                `).join('');
                document.getElementById('mainGrid').innerHTML = data.pack.map(u => createCard(u)).join('');
            }
            document.getElementById('loader').style.display = 'none';
        }

        function createCard(url) {
            return `
                <div class="img-card">
                    <div class="frame-container">
                        <img src="${url}">
                        <div class="manual-text">YOUR HEADLINE</div>
                        <img class="applied-logo" src="">
                    </div>
                    
                    <div class="tools">
                        <button class="tool-btn" onclick="toggleFilter(this, 'bright')">BRIGHT</button>
                        <button class="tool-btn" onclick="toggleFilter(this, 'pop')">POP</button>
                        <button class="tool-btn" onclick="toggleFilter(this, 'border')">BORDER</button>
                        <button class="tool-btn" style="color:var(--red)" onclick="this.closest('.img-card').remove()">DELETE</button>
                    </div>

                    <input type="text" placeholder="Headline text..." oninput="updateText(this)" style="width:100%; background:#000; border:1px solid var(--border); color:#fff; padding:10px; border-radius:8px;">
                    
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 15px;">
                        <button class="tool-btn" style="background:var(--blue); color:#000" onclick="alert('Downloading high-res YouTube version...')">DL YOUTUBE</button>
                        <button class="tool-btn" style="background:#fff; color:#000" onclick="alert('Downloading high-res TikTok version...')">DL TIKTOK</button>
                    </div>
                </div>`;
        }

        function updateText(input) {
            const overlay = input.closest('.img-card').querySelector('.manual-text');
            overlay.innerText = input.value;
            overlay.style.display = input.value ? 'block' : 'none';
        }

        function toggleFilter(btn, type) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            const container = card.querySelector('.frame-container');
            btn.classList.toggle('active');
            
            if(type === 'bright') img.style.filter = btn.classList.contains('active') ? 'brightness(1.3)' : 'none';
            if(type === 'pop') img.style.filter = btn.classList.contains('active') ? 'contrast(1.2) saturate(1.3)' : 'none';
            if(type === 'border') container.style.borderColor = btn.classList.contains('active') ? 'var(--mint)' : 'transparent';
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
        
        # 1. AI Extractions (Scanning whole video)
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 25})
        raw_frames = list(dict.fromkeys([i['url'] for i in ex.get('images', [])]))

        # 2. Pick 6 REAL Frames from center segment
        mid = len(raw_frames) // 3
        best_6 = raw_frames[mid:mid+6]

        s3.delete_object(Bucket=BUCKET, Key=fn)
        return jsonify({"status": "success", "pack": best_6, "library": raw_frames})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
