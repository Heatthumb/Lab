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
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; }
        .main-container { display: flex; height: 100vh; }
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); padding: 20px; display: none; overflow-y: auto; }
        .workspace { flex: 1; padding: 30px; overflow-y: auto; }
        .ctr-badge { background: linear-gradient(90deg, #00FFC2, #40E0FF); color: #000; padding: 4px 10px; border-radius: 4px; font-weight: 900; font-size: 10px; text-transform: uppercase; margin-bottom: 10px; display: inline-block; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 12px; position: relative; }
        .img-card img { width: 100%; border-radius: 8px; background: #000; }
        .logo-selector { display: flex; gap: 5px; flex-wrap: wrap; margin: 10px 0; }
        .logo-thumb { width: 40px; height: 40px; border: 1px solid var(--border); border-radius: 4px; cursor: pointer; object-fit: contain; }
        .logo-thumb.active { border-color: var(--mint); box-shadow: 0 0 5px var(--mint); }
        .controls { background: var(--card); border: 1px solid var(--border); border-radius: 15px; padding: 25px; max-width: 900px; margin: 0 auto 30px; }
        .btn-mint { background: var(--mint); color: #000; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; }
        .btn-blue { background: var(--blue); color: #000; border: none; padding: 6px; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 10px; }
        .loader { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); display:none; flex-direction:column; align-items:center; justify-content:center; z-index:9999; }
    </style>
</head>
<body>
    <div class="loader" id="loader"><h2 style="color:var(--mint)">PROCESSING NEURAL REQUEST</h2><p>Syncing subjects and applying logos...</p></div>

    <div class="main-container">
        <div class="sidebar" id="sidebar">
            <div class="ctr-badge">Unique Source Library</div>
            <div id="sideLibrary"></div>
        </div>

        <div class="workspace">
            <div id="labPanel">
                <div class="controls">
                    <div class="ctr-badge">Studio Controls</div>
                    <input type="file" id="videoFile" style="margin-bottom:10px;">
                    
                    <div style="background:#000; padding:15px; border-radius:10px; margin-bottom:15px;">
                        <label style="font-size:12px; color:var(--blue)">UPLOAD LOGOS (Click to select for usage)</label>
                        <input type="file" id="logoUpload" multiple onchange="handleLogoUpload(this)" style="margin-top:5px;">
                        <div id="globalLogoList" class="logo-selector"></div>
                    </div>

                    <button onclick="processVideo()" class="btn-mint">EXTRACT & AUTO-WORDING</button>
                </div>

                <div id="resultsSection" style="display:none;">
                    <div class="image-grid" id="mainGrid"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let uploadedLogos = [];

        function handleLogoUpload(input) {
            const files = Array.from(input.files);
            files.forEach(file => {
                const reader = new FileReader();
                reader.onload = e => {
                    uploadedLogos.push(e.target.result);
                    renderLogos();
                };
                reader.readAsDataURL(file);
            });
        }

        function renderLogos() {
            const html = uploadedLogos.map((src, i) => `
                <img src="${src}" class="logo-thumb active" onclick="this.classList.toggle('active')" data-index="${i}">
            `).join('');
            document.getElementById('globalLogoList').innerHTML = html;
        }

        async function processVideo() {
            const file = document.getElementById('videoFile').files[0];
            if(!file) return alert("Select video");
            document.getElementById('loader').style.display = 'flex';

            const formData = new FormData();
            formData.append('video', file);
            
            const res = await fetch('/process', { method: 'POST', body: formData });
            const data = await res.json();
            
            if(data.status === 'success') {
                document.getElementById('sidebar').style.display = 'block';
                document.getElementById('resultsSection').style.display = 'block';
                document.getElementById('mainGrid').innerHTML = data.pack.map(item => createCard(item.url, item.reason)).join('');
                // Filter sidebar for uniqueness
                const uniqueFrames = [...new Set(data.library)];
                document.getElementById('sideLibrary').innerHTML = uniqueFrames.map(u => `<img src="${u}" style="width:100%; border-radius:8px; margin-bottom:10px; cursor:pointer;" onclick="promote('${u}')">`).join('');
            }
            document.getElementById('loader').style.display = 'none';
        }

        function createCard(url, reason) {
            return `
                <div class="img-card">
                    <img src="${url}" class="main-img">
                    <div style="font-size:11px; margin:10px 0; color:#8A94A6;"><b>CTR Tip:</b> ${reason}</div>
                    <div class="card-tools">
                        <input type="text" class="mini-input" placeholder="Add specific words or change background...">
                        <div style="display:flex; align-items:center; gap:10px; margin:5px 0;">
                            <input type="checkbox" checked class="use-logo-check"> <span style="font-size:11px;">Apply Active Logos</span>
                        </div>
                        <div style="display:flex; gap:5px;">
                            <button class="btn-blue" style="flex:2" onclick="remixSingle(this)">FAST REMIX</button>
                            <button class="btn-mint" style="flex:1; font-size:10px;" onclick="window.open(this.closest('.img-card').querySelector('img').src)">SAVE</button>
                        </div>
                    </div>
                </div>`;
        }

        async function remixSingle(btn) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('.main-img');
            const prompt = card.querySelector('input').value;
            const useLogos = card.querySelector('.use-logo-check').checked;
            
            // Get active logos
            const activeLogos = Array.from(document.querySelectorAll('#globalLogoList .logo-thumb.active')).map(img => img.src);

            btn.innerText = "Processing...";
            const res = await fetch('/remix-single', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ 
                    url: img.src, 
                    prompt: prompt, 
                    logos: useLogos ? activeLogos : [] 
                })
            });
            const data = await res.json();
            if(data.url) img.src = data.url;
            btn.innerText = "FAST REMIX";
        }

        function promote(url) { document.getElementById('mainGrid').insertAdjacentHTML('afterbegin', createCard(url, "Custom Subject Promotion")); }
    </script>
</body>
</html>
"""

@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    fn = f"n_{int(time.time())}.mp4"
    try:
        s3.upload_fileobj(video, BUCKET, fn, ExtraArgs={'ACL': 'public-read'})
        v_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{fn}"
        
        # 1. Unique Frame Extraction
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 25})
        frames = list(dict.fromkeys([i['url'] for i in ex.get('images', [])])) # Remove duplicates

        pack = []
        # 2. Extract 6 frames and add AUTOMATIC wording immediately
        for i in range(min(6, len(frames))):
            r = fal_client.subscribe("fal-ai/flux-pro", {
                "image_url": frames[i],
                "prompt": "Keep original photo exactly the same but add a professional bold catchy headline text at the top or bottom related to the scene. Do not change the person or objects.",
                "strength": 0.4 # Low strength keeps the photo exactly the same
            })
            pack.append({"url": r['images'][0]['url'], "reason": "Auto-wording applied to source frame."})

        s3.delete_object(Bucket=BUCKET, Key=fn)
        return jsonify({"status": "success", "pack": pack, "library": frames})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/remix-single', methods=['POST'])
def remix_single():
    d = request.json
    logo_instr = "Add the provided logos into the scene naturally" if d['logos'] else ""
    r = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": d['url'],
        "prompt": f"Apply these changes: {d['prompt']}. {logo_instr}. Maintain the identity of the person and subject perfectly.",
        "strength": 0.45 # Balanced to allow changes but keep the door/person
    })
    return jsonify({"url": r['images'][0]['url']})

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
