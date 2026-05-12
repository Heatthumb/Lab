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
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --ghost: #8A94A6; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar: Current Scan vs History */
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .side-header { padding: 20px; border-bottom: 1px solid var(--border); font-weight: bold; color: var(--mint); }
        .scroll-area { flex: 1; overflow-y: auto; padding: 15px; }
        .history-section { border-top: 1px solid var(--border); padding: 15px; background: #0e1116; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; }
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 15px; margin-bottom: 20px; transition: 0.2s; }
        .img-card:hover { border-color: var(--mint); }
        .img-card img { width: 100%; border-radius: 8px; }
        
        .controls { background: var(--card); border: 1px solid var(--border); border-radius: 15px; padding: 25px; margin-bottom: 30px; }
        .btn-mint { background: var(--mint); color: #000; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; }
        .btn-blue { background: var(--blue); color: #000; border: none; padding: 8px; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 11px; }
        
        .logo-tray { display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap; }
        .logo-item { width: 45px; height: 45px; border: 2px solid var(--border); border-radius: 6px; cursor: pointer; }
        .logo-item.selected { border-color: var(--mint); box-shadow: 0 0 10px rgba(0,255,194,0.3); }
        
        .loader { position: fixed; inset: 0; background: rgba(0,0,0,0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
    </style>
</head>
<body>
    <div class="loader" id="loader"><h2 style="color:var(--mint)">NEURAL LOCK ACTIVE</h2><p>Preserving subjects & applying edits...</p></div>

    <div class="sidebar" id="sidebar" style="display:none;">
        <div class="side-header">CURRENT SCAN (RAW)</div>
        <div class="scroll-area" id="currentLibrary"></div>
        
        <div class="history-section">
            <div style="font-size:11px; color:var(--ghost); margin-bottom:10px;">SESSION HISTORY</div>
            <div id="historyLibrary" style="opacity: 0.5;"></div>
        </div>
    </div>

    <div class="workspace">
        <div id="authPanel" style="text-align:center; padding-top:100px;">
            <h1>HEATHUMB LAB V11</h1>
            <input type="password" id="passCode" placeholder="Access Code" style="padding:10px; border-radius:5px;">
            <button onclick="checkAuth()" class="btn-mint" style="width:150px;">ENTER</button>
        </div>

        <div id="labPanel" style="display:none;">
            <div class="controls">
                <div style="color:var(--mint); font-weight:bold; margin-bottom:15px;">1. UPLOAD SOURCES</div>
                <input type="file" id="videoFile" style="margin-bottom:15px; display:block;">
                
                <div style="background:#000; padding:15px; border-radius:10px; margin-bottom:20px;">
                    <label style="font-size:12px; color:var(--blue)">LOGO MANAGER (Click to activate)</label>
                    <input type="file" id="logoFiles" multiple onchange="loadLogos(this)" style="display:block; margin:10px 0;">
                    <div id="logoTray" class="logo-tray"></div>
                </div>

                <button onclick="processVideo()" class="btn-mint">DEEP SCAN VIDEO</button>
            </div>

            <div id="resultsArea">
                <div id="mainGrid" class="image-grid"></div>
            </div>
        </div>
    </div>

    <script>
        let logos = [];
        let sessionHistory = [];

        function checkAuth() { 
            if(document.getElementById('passCode').value === "{{ password }}") {
                document.getElementById('authPanel').style.display = 'none';
                document.getElementById('labPanel').style.display = 'block';
            }
        }

        function loadLogos(input) {
            Array.from(input.files).forEach(f => {
                const r = new FileReader();
                r.onload = e => { 
                    logos.push(e.target.result); 
                    renderLogos();
                };
                r.readAsDataURL(f);
            });
        }

        function renderLogos() {
            document.getElementById('logoTray').innerHTML = logos.map((s, i) => 
                `<img src="${s}" class="logo-item selected" onclick="this.classList.toggle('selected')">`
            ).join('');
        }

        async function processVideo() {
            const v = document.getElementById('videoFile').files[0];
            if(!v) return alert("Select video");
            
            // Move current library to history before starting new
            const currentLib = document.getElementById('currentLibrary').innerHTML;
            if(currentLib) {
                document.getElementById('historyLibrary').insertAdjacentHTML('afterbegin', currentLib);
            }

            document.getElementById('loader').style.display = 'flex';
            const fd = new FormData();
            fd.append('video', v);

            const res = await fetch('/process', { method: 'POST', body: fd });
            const data = await res.json();
            
            if(data.status === 'success') {
                document.getElementById('sidebar').style.display = 'flex';
                document.getElementById('currentLibrary').innerHTML = data.library.map(u => 
                    `<img src="${u}" style="width:100%; border-radius:5px; margin-bottom:8px; cursor:pointer;" onclick="promote('${u}')">`
                ).join('');
                document.getElementById('mainGrid').innerHTML = data.pack.map(item => createCard(item.url, item.reason)).join('');
            }
            document.getElementById('loader').style.display = 'none';
        }

        function createCard(url, reason) {
            return `
                <div class="img-card">
                    <img src="${url}">
                    <div style="font-size:11px; margin:10px 0; color:var(--ghost)">${reason}</div>
                    <div style="display:flex; gap:10px;">
                        <input type="text" placeholder="Add text/logos..." style="flex:1; background:#000; border:1px solid var(--border); color:#fff; padding:5px; border-radius:4px;">
                        <button class="btn-blue" onclick="remix(this)">REMIX</button>
                        <button class="btn-mint" style="width:60px; font-size:10px;" onclick="window.open('${url}')">SAVE</button>
                    </div>
                </div>`;
        }

        async function remix(btn) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            const prompt = card.querySelector('input').value;
            const activeLogos = Array.from(document.querySelectorAll('.logo-item.selected')).map(i => i.src);

            btn.innerText = "...";
            const res = await fetch('/remix', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: img.src, prompt: prompt, logos: activeLogos })
            });
            const d = await res.json();
            if(d.url) img.src = d.url;
            btn.innerText = "REMIX";
        }

        function promote(u) {
            document.getElementById('mainGrid').insertAdjacentHTML('afterbegin', createCard(u, "Manual Promotion"));
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
        
        # 1. RAW Extraction - No AI intervention here so pictures are REAL
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 25})
        raw_frames = list(dict.fromkeys([i['url'] for i in ex.get('images', [])]))

        pack = []
        # 2. Apply Wordings to the top 6 only
        for i in range(min(6, len(raw_frames))):
            r = fal_client.subscribe("fal-ai/flux-pro", {
                "image_url": raw_frames[i],
                "prompt": "Do not change the photo. Add a large, bold, professional YouTube-style headline text overlay that is easy to read.",
                "strength": 0.35 # LOWER STRENGTH = Keep the original photo exactly as it is
            })
            pack.append({"url": r['images'][0]['url'], "reason": "Strategic headline added to source."})

        s3.delete_object(Bucket=BUCKET, Key=fn)
        return jsonify({"status": "success", "pack": pack, "library": raw_frames})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/remix', methods=['POST'])
def remix():
    d = request.json
    r = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": d['url'],
        "prompt": f"{d['prompt']}. Include logos if provided. Keep the human and environment exactly as they appear in the original image.",
        "strength": 0.4
    })
    return jsonify({"url": r['images'][0]['url']})

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
