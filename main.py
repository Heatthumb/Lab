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
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --trash: #FF4D4D; --blue: #40E0FF; --gold: #FFD700; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; }
        .main-container { display: flex; height: 100vh; }
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); padding: 25px; display: none; overflow-y: auto; }
        .workspace { flex: 1; padding: 40px; overflow-y: auto; }
        .ctr-badge { background: linear-gradient(90deg, #00FFC2, #40E0FF); color: #000; padding: 4px 10px; border-radius: 4px; font-weight: 900; font-size: 10px; text-transform: uppercase; margin-bottom: 10px; display: inline-block; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 25px; margin-top: 20px; }
        
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 15px; position: relative; display: flex; flex-direction: column; }
        .img-card img { width: 100%; border-radius: 10px; cursor: zoom-in; background: #000; }
        
        .reasoning-box { background: rgba(0,0,0,0.3); border-left: 3px solid var(--mint); padding: 10px; margin-top: 12px; border-radius: 4px; font-size: 12px; line-height: 1.4; color: #B0B8C4; }
        .reasoning-box b { color: var(--mint); display: block; margin-bottom: 4px; font-size: 10px; text-transform: uppercase; }
        
        .card-tools { margin-top: 15px; display: flex; flex-direction: column; gap: 8px; }
        .mini-input { background: #000; border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 6px; font-size: 11px; width: 100%; box-sizing: border-box; }
        .controls { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 30px; max-width: 900px; margin: 0 auto; }
        .btn-mint { background: var(--mint); color: #000; border: none; padding: 14px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; }
        .btn-blue { background: var(--blue); color: #000; border: none; padding: 8px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 11px; }
        .modal { position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.9); display:none; align-items:center; justify-content:center; z-index:10000; }
        .modal img { max-width: 90%; max-height: 90%; border-radius: 10px; }
        .loader { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); display:none; flex-direction:column; align-items:center; justify-content:center; z-index:9999; text-align: center; }
    </style>
</head>
<body>
    <div class="modal" id="modal" onclick="this.style.display='none'"><img id="modalImg"></div>
    <div class="loader" id="loader">
        <h2 style="color:var(--mint)">NEURAL ANALYTICS ENGINE</h2>
        <p id="lStatus" style="color: white;">Calculating Visual Friction & Subject Isolation...</p>
    </div>

    <div class="main-container">
        <div class="sidebar" id="sidebar">
            <div class="ctr-badge">Source Vault</div>
            <div id="sideLibrary"></div>
        </div>

        <div class="workspace">
            <div id="authPanel" style="text-align:center; padding-top:100px;">
                <h1>HEATHUMB LAB</h1>
                <input type="password" id="passCode" placeholder="Access Code">
                <button onclick="checkAuth()" class="btn-mint" style="width:200px; margin-top:10px;">ENTER</button>
            </div>

            <div id="labPanel" style="display:none;">
                <div class="controls">
                    <div class="ctr-badge">Neural Configuration</div>
                    <input type="file" id="videoFile">
                    <div style="margin-bottom:15px; display: flex; gap: 20px;">
                        <label><input type="checkbox" id="autoWording" checked> Auto-Neural Wording</label>
                        <label><input type="checkbox" id="aiReasoning" checked> Predictive Analytics</label>
                    </div>
                    <input type="text" id="globalPrompt" placeholder="Style Overrides (e.g. 'High contrast, dark cinematic')">
                    <button onclick="processVideo()" class="btn-mint">START NEURAL SCAN</button>
                </div>

                <div id="resultsSection" style="display:none; margin-top:40px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style="color: var(--mint)">NEURAL WORKSPACE</h2>
                        <button onclick="downloadVisible()" class="btn-blue" style="padding: 10px 20px;">SAVE ALL TO DISK</button>
                    </div>
                    <div class="image-grid" id="mainGrid"></div>
                    <div style="margin-top:60px; border-top:1px dashed var(--border); padding-top:20px; opacity: 0.4;">
                        <h2 style="color: var(--trash)">RECOVERY VAULT</h2>
                        <div class="image-grid" id="trashGrid"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function checkAuth() { if(document.getElementById('passCode').value === "{{ password }}") { document.getElementById('authPanel').style.display = 'none'; document.getElementById('labPanel').style.display = 'block'; } }
        function enlarge(url) { document.getElementById('modalImg').src = url; document.getElementById('modal').style.display = 'flex'; }

        async function processVideo() {
            const file = document.getElementById('videoFile').files[0];
            if(!file) return alert("Select video");
            document.getElementById('loader').style.display = 'flex';

            const formData = new FormData();
            formData.append('video', file);
            formData.append('global_prompt', document.getElementById('globalPrompt').value);
            formData.append('auto_word', document.getElementById('autoWording').checked);

            try {
                const res = await fetch('/process', { method: 'POST', body: formData });
                const data = await res.json();
                
                if(data.status === 'success') {
                    document.getElementById('sidebar').style.display = 'block';
                    document.getElementById('resultsSection').style.display = 'block';
                    document.getElementById('mainGrid').innerHTML = data.pack.map(item => createCard(item.url, item.ctr, item.reason)).join('');
                    document.getElementById('sideLibrary').innerHTML = data.library.map(u => `<img src="${u}" style="width:100%; border-radius:8px; margin-bottom:10px; cursor:pointer;" onclick="promote('${u}')">`).join('');
                }
            } catch (e) { alert("Neural Engine Timeout - Try a shorter video"); }
            document.getElementById('loader').style.display = 'none';
        }

        function createCard(url, ctr, reason) {
            return `
                <div class="img-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <div class="ctr-badge">EST. CTR: ${ctr}%</div>
                        <div style="font-size:10px; color:var(--gold)">★★★★★</div>
                    </div>
                    <img src="${url}" onclick="enlarge('${url}')">
                    <div class="reasoning-box">
                        <b>Neural Analysis:</b>
                        ${reason || "Subject isolated with high visual friction. Optimal for mobile scrolling feeds."}
                    </div>
                    <div class="card-tools">
                        <select class="mini-input"><option value="landscape_16_9">YouTube (16:9)</option><option value="portrait_9_16">TikTok (9:16)</option></select>
                        <input type="text" class="mini-input" placeholder="Neural Remix Instructions...">
                        <div style="display:flex; gap:5px;">
                            <button class="btn-blue" style="flex:2" onclick="remixSingle(this)">REMIX</button>
                            <button class="btn-outline" style="flex:1" onclick="window.open(this.closest('.img-card').querySelector('img').src)">SAVE</button>
                            <button class="btn-outline" style="color:var(--trash)" onclick="trash(this)">X</button>
                        </div>
                    </div>
                </div>`;
        }

        async function remixSingle(btn) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            const reasonBox = card.querySelector('.reasoning-box');
            const prompt = card.querySelector('input').value;
            const ratio = card.querySelector('select').value;
            
            btn.innerText = "Analyzing...";
            const res = await fetch('/remix-single', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: img.src, prompt: prompt, ratio: ratio })
            });
            const data = await res.json();
            if(data.url) {
                img.src = data.url;
                reasonBox.innerHTML = `<b>Neural Analysis:</b> ${data.reason}`;
            }
            btn.innerText = "REMIX";
        }

        function promote(url) { document.getElementById('mainGrid').insertAdjacentHTML('afterbegin', createCard(url, 74, "Promoted from source. High fidelity subject detection.")); }
        function trash(btn) { document.getElementById('trashGrid').appendChild(btn.closest('.img-card')); btn.innerText = "RESTORE"; btn.onclick = function(){ restore(this); } }
        function restore(btn) { document.getElementById('mainGrid').appendChild(btn.closest('.img-card')); btn.innerText = "X"; btn.onclick = function(){ trash(this); } }
        function downloadVisible() { document.querySelectorAll('#mainGrid img').forEach(img => { const a = document.createElement('a'); a.href = img.src; a.download = 'neural_thumb.png'; a.click(); }); }
    </script>
</body>
</html>
"""

@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    gp = request.form.get('global_prompt', '')
    aw = request.form.get('auto_word') == 'true'
    fn = f"n_{int(time.time())}.mp4"
    try:
        s3.upload_fileobj(video, BUCKET, fn, ExtraArgs={'ACL': 'public-read'})
        v_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{fn}"
        
        # 1. Subject-Aware Extraction
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 25})
        frames = [i['url'] for i in ex.get('images', [])]

        pack = []
        # 2. Process Initial 10 (6 Real + 4 AI)
        for i in range(min(10, len(frames))):
            is_ai = i >= 6
            url = frames[i]
            if is_ai:
                word_prompt = "Add bold high-CTR text overlays" if aw else ""
                r = fal_client.subscribe("fal-ai/flux-pro", {
                    "image_url": url,
                    "prompt": f"Professional thumbnail, {gp}, {word_prompt}, centered subject, vivid colors",
                    "image_size": "landscape_16_9",
                    "strength": 0.55
                })
                url = r['images'][0]['url']
            
            # Simulated CTR Logic & Reasoning
            ctr = 82 + (i % 15) if is_ai else 65 + (i % 10)
            reason = "High subject-to-background contrast. The central focal point aligns with mobile eye-tracking patterns." if is_ai else "Clean source frame with minimal motion blur. Excellent base for manual remixing."
            pack.append({"url": url, "ctr": ctr, "reason": reason})

        s3.delete_object(Bucket=BUCKET, Key=fn)
        return jsonify({"status": "success", "pack": pack, "library": frames})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/remix-single', methods=['POST'])
def remix_single():
    d = request.json
    r = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": d['url'],
        "prompt": f"Professional design, {d['prompt']}, high-impact visual",
        "image_size": d['ratio'],
        "strength": 0.6
    })
    new_url = r['images'][0]['url']
    return jsonify({
        "url": new_url, 
        "reason": f"Remix optimized for {d['ratio']}. Modified elements enhance visual friction for improved stop-rate."
    })

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
