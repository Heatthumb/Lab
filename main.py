import os, boto3, fal_client, time
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
LAB_PASSWORD = os.environ.get("LAB_PASSWORD", "HEATHUMB2026")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "heatthumb-vault-sruli-259851212536-eu-north-1-an")

# --- MODERN LAB INTERFACE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar - The Frame Library */
        .sidebar { width: 300px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; padding: 20px; }
        .frame-item { width: 100%; border-radius: 12px; margin-bottom: 15px; cursor: pointer; border: 2px solid transparent; transition: 0.3s; }
        .frame-item:hover { border-color: var(--mint); transform: scale(1.02); }
        
        /* Main Workspace */
        .workspace { flex: 1; padding: 40px; overflow-y: auto; text-align: center; }
        .canvas-area { background: #000; border-radius: 24px; min-height: 400px; margin-bottom: 30px; display: flex; align-items: center; justify-content: center; border: 1px dashed var(--border); position: relative; }
        .canvas-area img { max-width: 100%; max-height: 500px; border-radius: 12px; }
        
        /* Controls */
        .controls { background: var(--card); padding: 25px; border-radius: 20px; border: 1px solid var(--border); max-width: 800px; margin: 0 auto; }
        .input-group { margin-bottom: 20px; text-align: left; }
        label { display: block; margin-bottom: 8px; color: #8A94A6; font-size: 12px; font-weight: bold; }
        select, input[type="text"] { width: 100%; padding: 12px; background: var(--carbon); border: 1px solid var(--border); color: white; border-radius: 8px; }
        
        .btn-mint { background: var(--mint); color: var(--carbon); font-weight: 800; padding: 15px 30px; border: none; border-radius: 12px; cursor: pointer; width: 100%; }
        
        /* Results Grid */
        .results-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 30px; }
        .result-card { background: var(--card); padding: 10px; border-radius: 15px; border: 1px solid var(--border); }
        .download-btn { background: #273140; color: white; border: none; padding: 8px; border-radius: 5px; margin-top: 10px; cursor: pointer; font-size: 11px; width: 100%; }
        
        .loading-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: none; align-items: center; justify-content: center; z-index: 100; }
    </style>
</head>
<body>
    <div class="loading-overlay" id="loader"><h1>GENERATING NEURAL ASSETS...</h1></div>

    <div class="sidebar">
        <h3 style="color: var(--mint)">SOURCE LIBRARY</h3>
        <p style="font-size: 11px; color: #8A94A6;">Select a base frame to remix</p>
        <div id="libraryItems">
            </div>
    </div>

    <div class="workspace">
        <div id="authBox">
            <h1 style="color: var(--mint)">HEATHUMB NEURAL LAB</h1>
            <input type="password" id="passCode" placeholder="Enter Access Code">
            <button onclick="checkAuth()" class="btn-mint" style="margin-top:20px;">UNLOCK LAB</button>
        </div>

        <div id="labBox" style="display:none;">
            <div class="controls">
                <div class="input-group">
                    <label>STEP 1: UPLOAD FOOTAGE</label>
                    <input type="file" id="videoFile" accept="video/*">
                </div>
                <div class="input-group" style="display:grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>
                        <label>DIMENSIONS</label>
                        <select id="format">
                            <option value="landscape_16_9">YouTube (16:9)</option>
                            <option value="portrait_9_16">TikTok / Reels (9:16)</option>
                            <option value="square_1_1">Instagram (1:1)</option>
                        </select>
                    </div>
                    <div>
                        <label>NEURAL STRENGTH</label>
                        <select id="strength">
                            <option value="0.3">Light Touch</option>
                            <option value="0.5" selected>Pro Remix</option>
                            <option value="0.8">Extreme AI</option>
                        </select>
                    </div>
                </div>
                <div class="input-group">
                    <label>AI MODIFICATIONS (OPTIONAL)</label>
                    <input type="text" id="aiPrompt" placeholder="e.g. Add a 'Next Day Delivery' badge, make background neon blue...">
                </div>
                <button onclick="processVideo()" class="btn-mint">START ANALYSIS</button>
            </div>

            <div class="results-grid" id="resultsGrid"></div>
        </div>
    </div>

    <script>
        let currentBaseImage = "";

        function checkAuth() {
            if(document.getElementById('passCode').value === "{{ password }}") {
                document.getElementById('authBox').style.display = 'none';
                document.getElementById('labBox').style.display = 'block';
            } else { alert("Invalid Code"); }
        }

        async function processVideo() {
            const file = document.getElementById('videoFile').files[0];
            if(!file) return alert("Select a video");
            
            document.getElementById('loader').style.display = 'flex';
            const formData = new FormData();
            formData.append('video', file);
            formData.append('prompt', document.getElementById('aiPrompt').value);
            formData.append('aspect_ratio', document.getElementById('format').value);

            const res = await fetch('/process', { method: 'POST', body: formData });
            const data = await res.json();
            document.getElementById('loader').style.display = 'none';

            if(data.status === 'success') {
                // Update Library
                const lib = document.getElementById('libraryItems');
                lib.innerHTML = "";
                data.full_library_20.forEach(url => {
                    lib.innerHTML += `<img src="${url}" class="frame-item" onclick="setBase('${url}')">`;
                });

                // Update Results
                const grid = document.getElementById('resultsGrid');
                grid.innerHTML = "";
                data.ai_remixes_4.forEach(url => {
                    grid.innerHTML += `
                        <div class="result-card">
                            <img src="${url}" style="width:100%; border-radius:10px;">
                            <button class="download-btn" onclick="window.open('${url}')">DOWNLOAD JPG</button>
                        </div>`;
                });
            }
        }
        
        function setBase(url) {
            currentBaseImage = url;
            alert("Base frame updated. Re-run analysis to use this frame.");
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
    user_prompt = request.form.get('prompt', '')
    aspect_ratio = request.form.get('aspect_ratio', 'landscape_16_9')
    
    filename = f"lab_{int(time.time())}.mp4"
    try:
        s3.upload_fileobj(video, BUCKET, filename, ExtraArgs={'ACL': 'public-read'})
        video_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{filename}"
        
        # 1. Extract Frames
        extract = fal_client.subscribe("fal-ai/ffmpeg-api/extract-frame", {"video_url": video_url, "count": 15})
        all_frames = [img['url'] for img in extract['images']]
        
        # 2. Neural Remix with user prompt
        remixes = []
        full_prompt = f"Professional YouTube thumbnail, {user_prompt}, high contrast, sharp details, cinematic lighting"
        
        for i in range(4):
            res = fal_client.subscribe("fal-ai/flux-pro", {
                "image_url": all_frames[0],
                "prompt": full_prompt,
                "image_size": aspect_ratio,
                "strength": 0.5
            })
            remixes.append(res['images'][0]['url'])
        
        s3.delete_object(Bucket=BUCKET, Key=filename)
        return jsonify({"status": "success", "ai_remixes_4": remixes, "full_library_20": all_frames})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
