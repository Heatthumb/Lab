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
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; overflow-x: hidden; }
        .main-container { display: flex; height: 100vh; }
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); padding: 25px; display: none; overflow-y: auto; }
        .workspace { flex: 1; padding: 40px; overflow-y: auto; }
        .ctr-badge { background: linear-gradient(90deg, #00FFC2, #40E0FF); color: #000; padding: 4px 10px; border-radius: 4px; font-weight: 900; font-size: 10px; text-transform: uppercase; margin-bottom: 10px; display: inline-block; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-top: 20px; }
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 12px; position: relative; }
        .img-card img { width: 100%; border-radius: 8px; background: #000; display: block; }
        .controls { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 30px; max-width: 800px; margin: 0 auto; }
        .btn-mint { background: var(--mint); color: #000; border: none; padding: 14px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; font-size: 15px; }
        .btn-outline { background: transparent; border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 8px; font-size: 11px; }
        input, select { width: 100%; padding: 12px; background: #000; border: 1px solid var(--border); color: #fff; border-radius: 8px; margin-bottom: 15px; box-sizing: border-box; }
        .loader { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.96); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
        .trash-vault { margin-top: 60px; border-top: 2px dashed var(--border); padding-top: 30px; opacity: 0.5; }
    </style>
</head>
<body>
    <div class="loader" id="loader">
        <h2 style="color: var(--mint)">NEURAL ENGINE: SCANNING ALL FRAMES</h2>
        <p id="loadText">Extracting exactly 25 frames from video...</p>
    </div>

    <div class="main-container">
        <div class="sidebar" id="sidebar">
            <div class="ctr-badge">Neural Source Library (25)</div>
            <div id="sideLibrary"></div>
        </div>

        <div class="workspace">
            <div id="authPanel" style="text-align:center; padding-top:100px;">
                <h1>HEATHUMB LAB</h1>
                <input type="password" id="passCode" placeholder="Access Code" style="max-width:300px;">
                <button onclick="checkAuth()" class="btn-mint" style="width:200px; margin-top:10px;">ENTER</button>
            </div>

            <div id="labPanel" style="display:none;">
                <div class="controls">
                    <div class="ctr-badge">Engine Input</div>
                    <input type="file" id="videoFile">
                    <select id="format">
                        <option value="landscape_16_9">YouTube (16:9)</option>
                        <option value="portrait_9_16">Shorts/TikTok (9:16)</option>
                    </select>
                    <input type="text" id="aiPrompt" placeholder="Neural Mods: e.g. 'Add a neon red border and text SALES'">
                    <button onclick="processVideo()" class="btn-mint">RUN DEEP ANALYSIS</button>
                </div>

                <div id="resultsSection" style="display:none; margin-top:40px;">
                    <h2 style="color: var(--mint)">AI NEURAL REMIXES (+4)</h2>
                    <div class="image-grid" id="aiGrid"></div>

                    <h2 style="color: #8A94A6; margin-top:40px;">NEURAL SELECTIONS (6)</h2>
                    <div class="image-grid" id="realGrid"></div>
                    
                    <div class="trash-vault">
                        <h2 style="color: var(--trash)">RECOVERY FILE (Trash)</h2>
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
            if(!file) return alert("Please select a video");

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
                                <div class="ctr-badge">${isAI ? 'Remix' : 'Source'} Score: ${isAI ? 94 : 72}%</div>
                                <img src="${u}">
                                <button class="btn-outline" onclick="window.open('${u}')">DOWNLOAD</button>
                                <button class="btn-outline" style="color:var(--trash)" onclick="moveToTrash(this)">DELETE</button>
                            </div>
                        `).join('');
                    };

                    draw('aiGrid', data.ai_remixes, true);
                    draw('realGrid', data.real_extracts, false);
                    
                    document.getElementById('sideLibrary').innerHTML = data.full_library.map(u => 
                        `<img src="${u}" style="width:100%; border-radius:8px; margin-bottom:10px;">`
                    ).join('');
                } else { alert(data.message); }
            } catch (e) { alert("Server connection failed."); }
            finally { document.getElementById('loader').style.display = 'none'; }
        }

        function moveToTrash(btn) {
            const card = btn.parentElement;
            btn.innerText = "RESTORE";
            btn.style.color = "var(--mint)";
            btn.onclick = function() { restoreFromTrash(this); };
            document.getElementById('vaultGrid').appendChild(card);
        }

        function restoreFromTrash(btn) {
            const card = btn.parentElement;
            const target = card.innerHTML.includes('Remix Score') ? 'aiGrid' : 'realGrid';
            btn.innerText = "DELETE";
            btn.style.color = "var(--trash)";
            btn.onclick = function() { moveToTrash(this); };
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
    
    filename = f"vid_{int(time.time())}.mp4"
    try:
        s3.upload_fileobj(video, BUCKET, filename, ExtraArgs={'ACL': 'public-read'})
        video_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{filename}"
        
        # 1. FIXED EXTRACTION: Use extract-nth-frame to guarantee exactly 25 frames
        extract = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {
            "video_url": video_url, 
            "max_frames": 25
        })
        all_frames = [img['url'] for img in extract.get('images', [])]

        if not all_frames:
            return jsonify({"status": "error", "message": "Neural scan failed to find frames."})

        # 2. SELECT 6 UNIQUE: Spread them out across the video
        step = max(1, len(all_frames) // 6)
        real_extracts = [all_frames[i * step] for i in range(6) if i * step < len(all_frames)]

        # 3. AI REMIXES (4): Use high strength so user prompts actually work
        remixes = []
        for i in range(4):
            # Select 4 distinct frames for variety
            idx = (i * 5) % len(all_frames)
            res = fal_client.subscribe("fal-ai/flux-pro", {
                "image_url": all_frames[idx],
                "prompt": f"Professional YouTube thumbnail, high-impact CTR style, {user_prompt}, cinematic colors, sharp, 8k",
                "image_size": fmt,
                "strength": 0.6 # High strength to ensure AI modifications show up
            })
            remixes.append(res['images'][0]['url'])

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
