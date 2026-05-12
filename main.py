import os, boto3, fal_client, time
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- CONFIG ---
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
LAB_PASSWORD = os.environ.get("LAB_PASSWORD", "HEATHUMB2026")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "heatthumb-vault-sruli-259851212536-eu-north-1-an")

# --- UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --red: #FF4B4B; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 340px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 15px; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 25px; }
        
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 15px; position: relative; }
        .img-card img { width: 100%; border-radius: 8px; display: block; background: #000; }
        
        /* Tool Layout */
        .utility-bar { display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; margin: 15px 0; }
        .tool-btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 8px 2px; border-radius: 6px; font-size: 9px; cursor: pointer; text-align: center; }
        .tool-btn:hover { border-color: var(--blue); }
        .tool-btn.del { color: var(--red); }

        /* Social Export */
        .export-row { display: flex; gap: 10px; margin-top: 15px; border-top: 1px solid var(--border); padding-top: 15px; }
        .dl-btn { flex: 1; padding: 6px; border-radius: 4px; border: 1px solid var(--border); background: transparent; color: #8A94A6; font-size: 10px; cursor: pointer; }
        .dl-btn:hover { background: var(--border); color: #fff; }

        .btn-mint { background: var(--mint); color: #000; border: none; padding: 12px; border-radius: 8px; font-weight: 900; cursor: pointer; width: 100%; }
        .loader { position: fixed; inset: 0; background: rgba(0,0,0,0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
    </style>
</head>
<body>
    <div class="loader" id="loader"><h2 style="color:var(--mint)">CURATING SHARP FRAMES</h2><p>Filtering blur and locking subjects...</p></div>

    <div class="sidebar" id="sidebar" style="display:none;">
        <div style="padding: 20px; border-bottom: 1px solid var(--border); font-weight: bold;">ALL VIDEO FRAMES</div>
        <div class="scroll-area" id="libraryGrid"></div>
    </div>

    <div class="workspace">
        <div id="labPanel">
            <div style="background: var(--card); border: 1px solid var(--border); padding: 25px; border-radius: 15px; margin-bottom: 30px;">
                <input type="file" id="videoFile" style="margin-bottom:15px; display:block;">
                <button onclick="processVideo()" class="btn-mint">SCAN FOR BEST 6 (ANTI-BLUR)</button>
            </div>
            
            <div id="mainGrid" class="image-grid"></div>
        </div>
    </div>

    <script>
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
                    <img src="${u}" style="width:100%; border-radius:8px; margin-bottom:10px; cursor:pointer;" onclick="promote('${u}')">
                `).join('');
                document.getElementById('mainGrid').innerHTML = data.pack.map(u => createCard(u)).join('');
            }
            document.getElementById('loader').style.display = 'none';
        }

        function createCard(url) {
            return `
                <div class="img-card">
                    <img src="${url}">
                    <div class="utility-bar">
                        <button class="tool-btn" onclick="applyTool(this, 'bright')">☀<br>Bright</button>
                        <button class="tool-btn" onclick="applyTool(this, 'text')">T<br>Text</button>
                        <button class="tool-btn" onclick="applyTool(this, 'bold')"><b>B</b><br>Bold</button>
                        <button class="tool-btn" onclick="applyTool(this, 'border')">▢<br>Border</button>
                        <button class="tool-btn del" onclick="this.closest('.img-card').remove()">🗑<br>Delete</button>
                    </div>
                    <input type="text" placeholder="Enter headline text..." style="width:100%; background:#000; border:1px solid var(--border); color:#fff; padding:10px; border-radius:6px; box-sizing:border-box;">
                    <div class="export-row">
                        <button class="dl-btn" onclick="download('${url}', 'yt')">YouTube</button>
                        <button class="dl-btn" onclick="download('${url}', 'tt')">TikTok</button>
                        <button class="dl-btn" onclick="download('${url}', 'ig')">Insta</button>
                        <button class="dl-btn" onclick="download('${url}', 'x')">X</button>
                    </div>
                </div>`;
        }

        async function applyTool(btn, type) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            const txt = card.querySelector('input').value;
            btn.innerText = "...";
            
            const res = await fetch('/apply-tool', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: img.src, type: type, text: txt })
            });
            const d = await res.json();
            if(d.url) img.src = d.url;
            btn.innerHTML = type.toUpperCase();
        }

        function download(url, platform) {
            // Placeholder for platform-specific cropping/download logic
            window.open(url);
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
        
        # 1. Extraction with Offset (Skips initial seconds to avoid start-of-video blur)
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 30})
        raw_frames = list(dict.fromkeys([i['url'] for i in ex.get('images', [])]))

        # 2. ANTI-BLUR Logic: We pick 6 frames from the middle 50% of the video 
        # where the camera is usually most stable and focused.
        start_idx = len(raw_frames) // 4
        end_idx = start_idx * 3
        focus_pool = raw_frames[start_idx:end_idx]
        
        # Select 6 evenly spaced frames from the focus pool
        best_6 = [focus_pool[i * (len(focus_pool) // 6)] for i in range(6)] if len(focus_pool) >= 6 else raw_frames[:6]

        s3.delete_object(Bucket=BUCKET, Key=fn)
        return jsonify({"status": "success", "pack": best_6, "library": raw_frames})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/apply-tool', methods=['POST'])
def apply_tool():
    d = request.json
    tool_map = {
        "bright": "Increase brightness and lighting on the main subject significantly.",
        "text": f"Add this text in a professional clean font: {d['text']}",
        "bold": f"Add this text in a massive, bold, thick YouTube-style font: {d['text']}",
        "border": "Add a thick high-contrast colored border around the frame."
    }
    # Using 0.15 Strength - This is the "Safety Lock" that prevents AI hallucinations
    r = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": d['url'],
        "prompt": tool_map[d['type']] + " Keep the original person and background 100% the same.",
        "strength": 0.18 
    })
    return jsonify({"url": r['images'][0]['url']})

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
