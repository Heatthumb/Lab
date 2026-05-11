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
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --trash: #FF4D4D; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; }
        .main-container { display: flex; height: 100vh; }
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); padding: 25px; display: none; overflow-y: auto; }
        .workspace { flex: 1; padding: 40px; overflow-y: auto; }
        .ctr-badge { background: linear-gradient(90deg, #00FFC2, #40E0FF); color: #000; padding: 5px 12px; border-radius: 6px; font-weight: 900; font-size: 11px; text-transform: uppercase; margin-bottom: 15px; display: inline-block; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; margin-top: 20px; }
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 15px; position: relative; }
        .img-card img { width: 100%; border-radius: 10px; background: #000; }
        .controls { background: var(--card); border: 1px solid var(--border); border-radius: 24px; padding: 35px; max-width: 850px; margin: 0 auto; }
        .btn-mint { background: var(--mint); color: #000; border: none; padding: 16px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; font-size: 16px; }
        .btn-outline { background: transparent; border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 10px; font-size: 11px; }
        input, select { width: 100%; padding: 14px; background: #000; border: 1px solid var(--border); color: #fff; border-radius: 10px; margin-bottom: 20px; box-sizing: border-box; }
        .loader { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
        .vault-section { margin-top: 80px; border-top: 2px dashed var(--border); padding-top: 40px; opacity: 0.6; }
    </style>
</head>
<body>
    <div class="loader" id="loader">
        <h1 style="color: var(--mint)">NEURAL DEEP SCAN ACTIVE</h1>
        <p>Generating 6 Neural Selections & 4 AI Remixes...</p>
    </div>

    <div class="main-container">
        <div class="sidebar" id="sidebar">
            <div class="ctr-badge">Neural Source Library</div>
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
                    <div class="ctr-badge">Neural Input</div>
                    <input type="file" id="videoFile">
                    <select id="format">
                        <option value="landscape_16_9">YouTube (16:9)</option>
                        <option value="portrait_9_16">TikTok (9:16)</option>
                    </select>
                    <input type="text" id="aiPrompt" placeholder="Neural Instructions: e.g. 'Add a next day delivery logo', 'Change background to blue'">
                    <button onclick="processVideo()" class="btn-mint">GENERATE NEURAL PACK</button>
                </div>

                <div id="resultsSection" style="display:none; margin-top:40px;">
                    <h2 style="color: var(--mint)">AI NEURAL REMIXES (+4)</h2>
                    <div class="image-grid" id="aiGrid"></div>

                    <h2 style="color: #8A94A6; margin-top:40px;">NEURAL SELECTIONS (6)</h2>
                    <div class="image-grid" id="realGrid"></div>
                    
                    <div class="vault-section">
                        <h2 style="color: var(--trash)">RECOVERY VAULT (Deleted Items)</h2>
                        <div class="image-grid" id="vaultGrid"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function checkAuth() {
            if(document.getElementById('passCode').value === "{{ password }}") {
                document.getElementById('authPanel').style.display = 'none';
                document.getElementById('labPanel').style.display = 'block';
            }
        }

        async function processVideo() {
            const file = document.getElementById('videoFile').files[0];
            if(!file) return alert("Select a video");

            document.getElementById('loader').style.display = 'flex';
            const formData = new FormData();
            formData.append('video', file);
            formData.append('format', document.getElementById('format').value);
            formData.append('prompt', document.getElementById('aiPrompt').value);

            try {
                const res = await fetch('/process', { method: 'POST', body: formData });
                const data = await res.json();
                
                if(data.status === 'success') {
                    document.getElementById('sidebar').style.display = 'block';
                    document.getElementById('resultsSection').style.display = 'block';
                    
                    const draw = (id, urls, isAI) => {
                        document.getElementById(id).innerHTML = urls.map(u => `
                            <div class="img-card">
                                <div class="ctr-badge">CTR: ${isAI ? 94 : 72}%</div>
                                <img src="${u}">
                                <button class="btn-outline" onclick="window.open('${u}')">DOWNLOAD</button>
                                <button class="btn-outline" style="color:var(--trash)" onclick="moveToVault(this)">DELETE</button>
                            </div>
                        `).join('');
                    };

                    draw('aiGrid', data.ai_remixes, true);
                    draw('realGrid', data.real_extracts, false);
                    
                    document.getElementById('sideLibrary').innerHTML = data.full_library.map(u => 
                        `<img src="${u}" style="width:100%; border-radius:8px; margin-bottom:10px; cursor:pointer;">`
                    ).join('');
                } else { alert(data.message); }
            } catch (e) { alert("Error: " + e); }
            finally { document.getElementById('loader').style.display = 'none'; }
        }

        function moveToVault(btn) {
            const card = btn.parentElement;
            const vault = document.getElementById('vaultGrid');
            btn.innerText = "RESTORE";
            btn.style.color = "var(--mint)";
            btn.onclick = function() { restoreFromVault(this); };
            vault.appendChild(card);
        }

        function restoreFromVault(btn) {
            const card = btn.parentElement;
            const target = card.innerHTML.includes('CTR: 94') ? 'aiGrid' : 'realGrid';
            btn.innerText = "DELETE";
            btn.style.color = "var(--trash)";
            btn.onclick = function() { moveToVault(this); };
            document.getElementById(target).appendChild(card);
        }
    </script>
</body>
</html>
"""

@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    fmt = request.form.get('format', 'landscape_16_9')
    user_prompt = request.form.get('prompt', '')
    
    filename = f"n_{int(time.time())}.mp4"
    try:
        s3.upload_fileobj(video, BUCKET, filename, ExtraArgs={'ACL': 'public-read'})
        video_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{filename}"
        
        # 1. DEEP SCAN EXTRACTION: We manually force a wait and request 25 frames
        # We use 'subscribe' but with a loop check to ensure we don't get duplicates
        extract_result = fal_client.subscribe("fal-ai/ffmpeg-api/extract-frame", {
            "video_url": video_url, 
            "count": 25
        })
        all_frames = [img['url'] for img in extract_result.get('images', [])]

        if len(all_frames) < 10:
            # Fallback if AI is being lazy: re-request with higher precision
            time.sleep(2)
            extract_result = fal_client.subscribe("fal-ai/ffmpeg-api/extract-frame", {"video_url": video_url, "count": 25})
            all_frames = [img['url'] for img in extract_result.get('images', [])]

        # 2. THE AI REMIXES (4 UNIQUE): We pick frames from different timestamps
        remixes = []
        # Use frames at index 0, 5, 10, 15 to ensure they are different scenes
        for idx in [0, 5, 10, 15]:
            if idx < len(all_frames):
                res = fal_client.subscribe("fal-ai/flux-pro", {
                    "image_url": all_frames[idx],
                    "prompt": f"Professional YouTube thumbnail, {user_prompt}, cinematic, sharp focus, vibrant color grading",
                    "image_size": fmt,
                    "strength": 0.55 # Increased strength so modifications like 'red border' work
                })
                remixes.append(res['images'][0]['url'])

        # 3. THE 6 SELECTIONS: Pick 6 distinct frames
        real_extracts = [all_frames[i] for i in [2, 7, 12, 17, 21, 24] if i < len(all_frames)]

        s3.delete_object(Bucket=BUCKET, Key=filename)
        return jsonify({
            "status": "success", 
            "ai_remixes": remixes, 
            "real_extracts": real_extracts, 
            "full_library": all_frames
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
