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
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; }
        
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 15px; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; }
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 15px; margin-bottom: 20px; }
        .img-card img { width: 100%; border-radius: 8px; margin-bottom: 10px; }
        
        .lib-item { position: relative; margin-bottom: 10px; }
        .lib-item img { width: 100%; border-radius: 6px; }
        .plus-btn { position: absolute; top: 5px; right: 5px; background: var(--mint); color: #000; border: none; border-radius: 50%; width: 25px; height: 25px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }
        .plus-btn:hover { transform: scale(1.1); background: #fff; }

        .controls { background: var(--card); border: 1px solid var(--border); border-radius: 15px; padding: 25px; margin-bottom: 30px; }
        .btn-mint { background: var(--mint); color: #000; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; }
        .btn-blue { background: var(--blue); color: #000; border: none; padding: 8px; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 11px; }
        .loader { position: fixed; inset: 0; background: rgba(0,0,0,0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
    </style>
</head>
<body>
    <div class="loader" id="loader"><h2 style="color:var(--mint)">NEURAL EXTRACTION ACTIVE</h2><p>Scanning video subjects...</p></div>

    <div class="sidebar" id="sidebar" style="display:none;">
        <div style="padding: 20px; border-bottom: 1px solid var(--border); font-weight: bold;">SOURCE LIBRARY</div>
        <div class="scroll-area" id="libraryGrid"></div>
    </div>

    <div class="workspace">
        <div id="authPanel" style="text-align:center; padding-top:100px;">
            <h1>HEATHUMB LAB V12</h1>
            <input type="password" id="passCode" placeholder="Access Code">
            <button onclick="checkAuth()" class="btn-mint" style="width:150px;">ENTER</button>
        </div>

        <div id="labPanel" style="display:none;">
            <div class="controls">
                <input type="file" id="videoFile" style="margin-bottom:15px; display:block;">
                <button onclick="processVideo()" class="btn-mint">DEEP SCAN VIDEO</button>
            </div>

            <div id="mainGrid"></div>
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
            const v = document.getElementById('videoFile').files[0];
            if(!v) return alert("Select video");
            
            document.getElementById('loader').style.display = 'flex';
            const fd = new FormData();
            fd.append('video', v);

            const res = await fetch('/process', { method: 'POST', body: fd });
            const data = await res.json();
            
            if(data.status === 'success') {
                document.getElementById('sidebar').style.display = 'flex';
                // 1. Populate Library with + button
                document.getElementById('libraryGrid').innerHTML = data.library.map(u => `
                    <div class="lib-item">
                        <img src="${u}">
                        <button class="plus-btn" onclick="promote('${u}')">+</button>
                    </div>
                `).join('');
                
                // 2. Automatically populate Workspace with the 6 word-ready frames
                document.getElementById('mainGrid').innerHTML = data.pack.map(item => createCard(item.url, item.reason)).join('');
            }
            document.getElementById('loader').style.display = 'none';
        }

        function createCard(url, reason) {
            return `
                <div class="img-card">
                    <img src="${url}">
                    <div style="font-size:11px; margin-bottom:10px; color:#8A94A6;">${reason}</div>
                    <div style="display:flex; gap:10px;">
                        <input type="text" placeholder="Add text/logos..." style="flex:1; background:#000; border:1px solid var(--border); color:#fff; padding:5px; border-radius:4px;">
                        <button class="btn-blue" onclick="remix(this)">REMIX</button>
                        <button class="btn-mint" style="width:60px; font-size:10px;" onclick="window.open('${url}')">SAVE</button>
                    </div>
                </div>`;
        }

        function promote(u) {
            document.getElementById('mainGrid').insertAdjacentHTML('afterbegin', createCard(u, "Added from Library"));
        }

        async function remix(btn) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            const prompt = card.querySelector('input').value;

            btn.innerText = "...";
            const res = await fetch('/remix', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: img.src, prompt: prompt })
            });
            const d = await res.json();
            if(d.url) img.src = d.url;
            btn.innerText = "REMIX";
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
        
        # 1. Extraction
        ex = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {"video_url": v_url, "max_frames": 25})
        raw_frames = list(dict.fromkeys([i['url'] for i in ex.get('images', [])]))

        # 2. Workspace Population (Auto-Wordings)
        pack = []
        for i in range(min(6, len(raw_frames))):
            r = fal_client.subscribe("fal-ai/flux-pro", {
                "image_url": raw_frames[i],
                "prompt": "Keep the original photo exactly as it is. Add a professional, large, high-contrast YouTube headline text overlay.",
                "strength": 0.35 # Lock the original photo
            })
            pack.append({"url": r['images'][0]['url'], "reason": "Auto-optimized for CTR."})

        s3.delete_object(Bucket=BUCKET, Key=fn)
        return jsonify({"status": "success", "pack": pack, "library": raw_frames})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/remix', methods=['POST'])
def remix():
    d = request.json
    r = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": d['url'],
        "prompt": f"{d['prompt']}. Do not change the person or the background layout. Just add requested elements.",
        "strength": 0.4
    })
    return jsonify({"url": r['images'][0]['url']})

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
