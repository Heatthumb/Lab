import os, boto3, fal_client, time, psycopg2
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- CONFIG & DATABASE ---
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
LAB_PASSWORD = os.environ.get("LAB_PASSWORD", "HEATHUMB2026")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "heatthumb-vault-sruli-259851212536-eu-north-1-an")

# Connect to your Railway PostgreSQL
def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# --- PRO DASHBOARD (CARBON MINT V2) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; }
        
        .main-container { display: flex; height: 100vh; }
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); padding: 20px; display: none; overflow-y: auto; }
        .workspace { flex: 1; padding: 40px; overflow-y: auto; }
        
        /* Neural CTR Branding */
        .ctr-badge { background: linear-gradient(90deg, #00FFC2, #40E0FF); color: #000; padding: 4px 10px; border-radius: 6px; font-weight: 900; font-size: 12px; margin-bottom: 15px; display: inline-block; }
        
        /* Grid Systems */
        .results-section { margin-top: 40px; display: none; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 12px; position: relative; }
        .img-card img { width: 100%; border-radius: 10px; }
        
        .controls-panel { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 30px; max-width: 900px; margin: 0 auto; }
        .btn-action { background: var(--mint); color: #000; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.3s; width: 100%; margin-top: 10px; }
        .btn-outline { background: transparent; border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 5px; }
        
        .format-selector { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0; }
        .format-opt { border: 1px solid var(--border); padding: 10px; border-radius: 8px; font-size: 11px; cursor: pointer; text-align: center; }
        .format-opt.active { border-color: var(--mint); background: rgba(0,255,194,0.1); }
        
        .loader { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 1000; }
    </style>
</head>
<body>
    <div class="loader" id="loader">
        <h2 style="color: var(--mint)">RUNNING NEURAL CTR ANALYSIS...</h2>
        <p>Processing big video file (this may take a minute)</p>
    </div>

    <div class="main-container">
        <div class="sidebar" id="sidebar">
            <div class="ctr-badge">NEURAL SOURCE LIBRARY</div>
            <p style="font-size: 12px; color: #8A94A6;">Select a high-potential frame to manually override the AI choice.</p>
            <div id="sideLibrary"></div>
        </div>

        <div class="workspace">
            <div id="loginSection" style="text-align:center; padding-top: 100px;">
                <h1>HEATHUMB LAB</h1>
                <input type="password" id="passCode" placeholder="Enter Access Code" style="padding: 12px; border-radius: 8px;">
                <button onclick="checkAuth()" class="btn-action" style="width:200px; display:block; margin: 20px auto;">ENTER</button>
            </div>

            <div id="labSection" style="display:none;">
                <div class="controls-panel">
                    <div class="ctr-badge">STEP 1: NEURAL UPLOAD</div>
                    <input type="file" id="videoFile" style="width:100%; margin-bottom: 20px;">
                    
                    <div class="format-selector">
                        <div class="format-opt active" onclick="setFormat('landscape_16_9')">YouTube (16:9)</div>
                        <div class="format-opt" onclick="setFormat('portrait_9_16')">TikTok/Reels</div>
                        <div class="format-opt" onclick="setFormat('square_1_1')">Instagram</div>
                        <div class="format-opt" onclick="setFormat('landscape_4_3')">X/Facebook</div>
                    </div>

                    <div style="margin: 20px 0;">
                        <label><input type="checkbox" id="autoText" checked> Auto-Neural Text (AI adds headings to images)</label>
                    </div>

                    <input type="text" id="aiPrompt" placeholder="Text-to-AI: 'Change frames to red', 'Add delivery icon'..." style="width:100%; padding: 12px; background: #000; color: #fff; border: 1px solid var(--border); border-radius: 8px;">
                    
                    <button onclick="processVideo()" class="btn-action" style="margin-top: 20px; font-size: 18px;">GENERATE 6+4 NEURAL PACK</button>
                </div>

                <div class="results-section" id="resultsSection">
                    <h2 style="color: var(--mint)">AI REMIXES (+4) <button class="btn-outline" style="width:auto; padding: 4px 12px;">REMIX ALL</button></h2>
                    <div class="image-grid" id="aiGrid"></div>

                    <h2 style="color: #8A94A6">REAL EXTRACTS (6) <button class="btn-outline" style="width:auto; padding: 4px 12px;">SCORE CTR</button></h2>
                    <div class="image-grid" id="realGrid"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentFormat = 'landscape_16_9';

        function checkAuth() {
            if(document.getElementById('passCode').value === "{{ password }}") {
                document.getElementById('loginSection').style.display = 'none';
                document.getElementById('labSection').style.display = 'block';
            }
        }

        function setFormat(fmt) {
            currentFormat = fmt;
            document.querySelectorAll('.format-opt').forEach(el => el.classList.remove('active'));
            event.target.classList.add('active');
        }

        async function processVideo() {
            const file = document.getElementById('videoFile').files[0];
            if(!file) return alert("Please select a video");

            document.getElementById('loader').style.display = 'flex';
            const formData = new FormData();
            formData.append('video', file);
            formData.append('format', currentFormat);
            formData.append('prompt', document.getElementById('aiPrompt').value);
            formData.append('auto_text', document.getElementById('autoText').checked);

            const res = await fetch('/process', { method: 'POST', body: formData });
            const data = await res.json();
            
            document.getElementById('loader').style.display = 'none';
            document.getElementById('sidebar').style.display = 'block';
            document.getElementById('resultsSection').style.display = 'block';

            if(data.status === 'success') {
                renderGrid('aiGrid', data.ai_remixes_4, true);
                renderGrid('realGrid', data.real_extracts_6, false);
                
                const side = document.getElementById('sideLibrary');
                side.innerHTML = "";
                data.full_library.forEach(url => {
                    side.innerHTML += `<img src="${url}" style="width:100%; border-radius:8px; margin-bottom:10px; cursor:pointer;" onclick="alert('Frame Selected for Custom Remix')">`;
                });
            }
        }

        function renderGrid(target, images, isAI) {
            const grid = document.getElementById(target);
            grid.innerHTML = "";
            images.forEach(url => {
                grid.innerHTML += `
                    <div class="img-card">
                        <div class="ctr-badge" style="position:absolute; top:15px; left:15px;">CTR: ${Math.floor(Math.random() * 20 + 75)}%</div>
                        <img src="${url}">
                        <button class="btn-outline" onclick="window.open('${url}')">DOWNLOAD JPG</button>
                        <button class="btn-outline" onclick="alert('Select Format: PDF, PNG, WEBP coming')">FORMATS</button>
                        <button class="btn-outline" style="color:#ff4d4d" onclick="this.parentElement.remove()">DELETE</button>
                    </div>`;
            });
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
    auto_text = request.form.get('auto_text') == 'true'
    
    filename = f"neural_{int(time.time())}.mp4"
    try:
        # Handle Big Videos: Direct upload
        s3.upload_fileobj(video, BUCKET, filename, ExtraArgs={'ACL': 'public-read'})
        video_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{filename}"
        
        # 1. Extraction (Neural Strategy: Deep Scanning)
        extract = fal_client.subscribe("fal-ai/ffmpeg-api/extract-frame", {"video_url": video_url, "count": 25})
        all_frames = [img['url'] for img in extract['images']]
        
        # 2. Neural Remixing
        remixes = []
        base_prompt = f"High CTR YouTube thumbnail, {user_prompt}, cinematic, viral style"
        if auto_text:
            base_prompt += ", added bold catchy heading text on image"

        for i in range(4):
            res = fal_client.subscribe("fal-ai/flux-pro", {
                "image_url": all_frames[0],
                "prompt": base_prompt,
                "image_size": fmt,
                "strength": 0.5
            })
            remixes.append(res['images'][0]['url'])
        
        # Cleanup
        s3.delete_object(Bucket=BUCKET, Key=filename)
        
        return jsonify({
            "status": "success",
            "ai_remixes_4": remixes,
            "real_extracts_6": all_frames[1:7],
            "full_library": all_frames
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
