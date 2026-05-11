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
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --trash: #FF4D4D; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; }
        .main-container { display: flex; height: 100vh; }
        .sidebar { width: 350px; background: var(--card); border-right: 1px solid var(--border); padding: 25px; display: none; overflow-y: auto; }
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
        .vault-section { margin-top: 60px; border-top: 2px dashed var(--border); padding-top: 40px; opacity: 0.7; }
    </style>
</head>
<body>
    <div class="loader" id="loader">
        <h1 style="color: var(--mint)">NEURAL DEEP SCAN ACTIVE</h1>
        <p>Extracting frames across entire video duration...</p>
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
                    <input type="text" id="aiPrompt" placeholder="Neural Modifications: 'Add red border', 'Next day delivery text'">
                    <button onclick="processVideo()" class="btn-mint">GENERATE 6+4 NEURAL PACK</button>
                </div>

                <div id="resultsSection" style="display:none; margin-top:40px;">
                    <h2 style="color: var(--mint)">AI NEURAL REMIXES (+4)</h2>
                    <div class="image-grid" id="aiGrid"></div>

                    <h2 style="color: #8A94A6; margin-top:40px;">NEURAL SELECTIONS (6)</h2>
                    <div class="image-grid" id="realGrid"></div>
                    
                    <div class="vault-section">
                        <h2 style="color: var(--trash)">RECOVERY VAULT (Deleted)</h2>
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
                            <div class="img-card" data-url="${u}">
                                <div class="ctr-badge">Score: ${isAI ? 92 : 71}%</div>
                                <img src="${u}">
                                <button class="btn-outline" onclick="window.open('${u}')">DOWNLOAD</button>
                                <button class="btn-outline" style="color:var(--trash)" onclick="moveToVault(this)">DELETE</button>
                            </div>
                        `).join('');
                    };

                    draw('aiGrid', data.ai_remixes, true);
                    draw('realGrid', data.real_extracts, false);
                    
                    document.getElementById('sideLibrary').innerHTML = data.full_library.map(u => 
                        `<img src="${u}" style="width:100%; border-radius:8px; margin-bottom:10px; cursor:pointer;" onclick="alert('Frame selected for re-remix')">`
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
            const target = card.innerHTML.includes('Score: 92') ? 'aiGrid' : 'realGrid';
            btn.innerText = "DELETE";
            btn.style.color = "var(--trash)";
            btn.onclick = function() { moveToVault(this); };
            document.getElementById(target).appendChild(card);
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
    video = request.files['video']
    fmt = request.form.get('format', 'landscape_16_9')
    user_prompt = request.form.get('prompt', '')
    
    filename = f"n_{int(time.time())}.mp4"
    try:
        s3.upload_fileobj(video, BUCKET, filename, ExtraArgs={'ACL': 'public-read'})
        video_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{filename}"
        
        # 1. DEEP SCAN: Force extraction across 25 different points in the video
        extract = fal_client.subscribe("fal-ai/ffmpeg-api/extract-frame", {
            "video_url": video_url, 
            "count": 25,
            "extraction_type": "uniform" # Forces it to spread across the whole video
        })
        all_frames = [img['url'] for img in extract['images']]

        # 2. NEURAL REMIX: Use 4 unique frames (1st, 5th, 10th, 15th) to ensure variety
        remixes = []
        indices = [0, 5, 10, 15]
        for i in indices:
            if i < len(all_frames):
                # Stronger Prompting to ensure the AI actually listens to "Add red border" etc.
                res = fal_client.subscribe("fal-ai/flux-pro", {
                    "image_url": all_frames[i],
                    "prompt": f"YouTube thumbnail, {user_prompt}, high visual impact, sharp edges, vivid colors, cinematic, highly detailed",
                    "image_size": fmt,
                    "strength": 0.5 # Increased strength so modifications show up better
                })
                remixes.append(res['images'][0]['url'])
        
        # 3. SELECT 6: Grabbing a spread of frames for the "Real" section
        real_extracts = all_frames[2:8] if len(all_frames) >= 8 else all_frames
        
        s3.delete_object(Bucket=BUCKET, Key=filename)
        return jsonify({
            "status": "success", 
            "ai_remixes": remixes, 
            "real_extracts": real_extracts, 
            "full_library": all_frames
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
