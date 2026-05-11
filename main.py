import os, boto3, fal_client, time, psycopg2
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --trash: #FF4D4D; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; }
        .main-container { display: flex; height: 100vh; }
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); padding: 25px; display: none; overflow-y: auto; }
        .workspace { flex: 1; padding: 40px; overflow-y: auto; }
        .ctr-badge { background: linear-gradient(90deg, #00FFC2, #40E0FF); color: #000; padding: 5px 12px; border-radius: 6px; font-weight: 900; font-size: 11px; text-transform: uppercase; margin-bottom: 15px; display: inline-block; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; margin-top: 20px; }
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 15px; position: relative; }
        .img-card img { width: 100%; border-radius: 10px; background: #000; min-height: 150px; }
        .controls { background: var(--card); border: 1px solid var(--border); border-radius: 24px; padding: 35px; max-width: 850px; margin: 0 auto; }
        .btn-mint { background: var(--mint); color: #000; border: none; padding: 16px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; font-size: 16px; transition: 0.3s; }
        .btn-mint:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(0,255,194,0.3); }
        .btn-outline { background: transparent; border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 10px; font-size: 11px; }
        input, select { width: 100%; padding: 14px; background: #000; border: 1px solid var(--border); color: #fff; border-radius: 10px; margin-bottom: 20px; box-sizing: border-box; }
        .loader { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.98); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; text-align: center; }
        .vault-section { margin-top: 60px; border-top: 2px dashed var(--border); padding-top: 40px; opacity: 0.6; }
    </style>
</head>
<body>
    <div class="loader" id="loader">
        <h1 style="color: var(--mint)">NEURAL ENGINE ACTIVE</h1>
        <p id="statusMsg">Uploading to Cloud Vault...</p>
        <div style="width: 200px; height: 4px; background: #222; border-radius: 10px; margin-top: 20px;">
            <div id="progressBar" style="width: 10%; height: 100%; background: var(--mint); border-radius: 10px; transition: 1s;"></div>
        </div>
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
                    <input type="text" id="aiPrompt" placeholder="Neural Mods: e.g. 'Add bright red border', 'Add 24h delivery sticker'">
                    <button onclick="processVideo()" class="btn-mint">START DEEP SCAN</button>
                </div>

                <div id="resultsSection" style="display:none; margin-top:40px;">
                    <h2 style="color: var(--mint)">AI NEURAL REMIXES (+4)</h2>
                    <div class="image-grid" id="aiGrid"></div>

                    <h2 style="color: #8A94A6; margin-top:40px;">NEURAL SELECTIONS (6)</h2>
                    <div class="image-grid" id="realGrid"></div>
                    
                    <div class="vault-section">
                        <h2 style="color: var(--trash)">RECOVERY VAULT</h2>
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
            if(!file) return alert("Please select a video file first.");

            document.getElementById('loader').style.display = 'flex';
            const formData = new FormData();
            formData.append('video', file);
            formData.append('format', document.getElementById('format').value);
            formData.append('prompt', document.getElementById('aiPrompt').value);

            // Heartbeat Status Updates
            const updateStatus = (msg, percent) => {
                document.getElementById('statusMsg').innerText = msg;
                document.getElementById('progressBar').style.width = percent + '%';
            };

            updateStatus("Uploading Video...", 30);

            try {
                const res = await fetch('/process', { method: 'POST', body: formData });
                updateStatus("AI Engine Processing...", 60);
                
                const data = await res.json();
                
                if(data.status === 'success') {
                    updateStatus("Rendering Results...", 90);
                    document.getElementById('sidebar').style.display = 'block';
                    document.getElementById('resultsSection').style.display = 'block';
                    
                    const draw = (id, urls, isAI) => {
                        document.getElementById(id).innerHTML = urls.map(u => `
                            <div class="img-card">
                                <div class="ctr-badge">Score: ${isAI ? 94 : 68}%</div>
                                <img src="${u}">
                                <button class="btn-outline" onclick="window.open('${u}')">DOWNLOAD</button>
                                <button class="btn-outline" style="color:var(--trash)" onclick="moveToVault(this)">DELETE</button>
                            </div>
                        `).join('');
                    };

                    draw('aiGrid', data.ai_remixes, true);
                    draw('realGrid', data.real_extracts, false);
                    
                    document.getElementById('sideLibrary').innerHTML = data.full_library.map(u => 
                        `<img src="${u}" style="width:100%; border-radius:8px; margin-bottom:10px; cursor:pointer;" onclick="alert('Frame Selected for Custom AI Job')">`
                    ).join('');

                } else { throw new Error(data.message); }
            } catch (e) {
                alert("Neural Error: " + e.message);
            } finally {
                document.getElementById('loader').style.display = 'none';
            }
        }

        function moveToVault(btn) {
            const card = btn.parentElement;
            btn.innerText = "RESTORE";
            btn.style.color = "var(--mint)";
            btn.onclick = function() { restoreFromVault(this); };
            document.getElementById('vaultGrid').appendChild(card);
        }

        function restoreFromVault(btn) {
            const card = btn.parentElement;
            const isAI = card.innerHTML.includes('Score: 94');
            btn.innerText = "DELETE";
            btn.style.color = "var(--trash)";
            btn.onclick = function() { moveToVault(this); };
            document.getElementById(isAI ? 'aiGrid' : 'realGrid').appendChild(card);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

@app.route('/process', methods=['POST'])
def process():
    if 'video' not in request.files:
        return jsonify({"status": "error", "message": "No video file found in request"})
        
    video = request.files['video']
    fmt = request.form.get('format', 'landscape_16_9')
    user_prompt = request.form.get('prompt', '')
    
    filename = f"lab_{int(time.time())}.mp4"
    try:
        # 1. S3 Upload
        s3.upload_fileobj(video, BUCKET, filename, ExtraArgs={'ACL': 'public-read'})
        video_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{filename}"
        
        # 2. Deep Extraction (The 6 Selections)
        # We extract 25 frames, then pick a spread to ensure they aren't all the same
        extract = fal_client.subscribe("fal-ai/ffmpeg-api/extract-frame", {
            "video_url": video_url, 
            "count": 25
        })
        all_frames = [img['url'] for img in extract['images']]

        if len(all_frames) < 1:
            return jsonify({"status": "error", "message": "Video scanning failed. Try a different format."})

        # 3. AI Remixing (The 4 Remixes)
        remixes = []
        # We pick 4 distinct frames from the 25 for variety
        step = max(1, len(all_frames) // 4)
        for i in range(4):
            frame_idx = i * step
            if frame_idx < len(all_frames):
                res = fal_client.subscribe("fal-ai/flux-pro", {
                    "image_url": all_frames[frame_idx],
                    "prompt": f"Professional YouTube thumbnail design, {user_prompt}, cinematic lighting, high-end commercial photography, sharp focus, 8k",
                    "image_size": fmt,
                    "strength": 0.5
                })
                remixes.append(res['images'][0]['url'])
        
        # Select 6 distinct frames for the "Real Selections" grid
        real_extracts = [all_frames[i] for i in range(0, min(len(all_frames), 18), 3)]
        
        s3.delete_object(Bucket=BUCKET, Key=filename)
        return jsonify({
            "status": "success", 
            "ai_remixes": remixes, 
            "real_extracts": real_extracts[:6], 
            "full_library": all_frames
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
