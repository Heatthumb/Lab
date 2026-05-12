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
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar & History */
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 15px; }
        .history-pane { height: 200px; border-top: 1px solid var(--border); background: #0e1116; padding: 10px; overflow-y: auto; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; }
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 15px; margin-bottom: 25px; position: relative; }
        .img-card img { width: 100%; border-radius: 8px; border: 1px solid #000; }
        
        .lib-item { position: relative; margin-bottom: 12px; border-radius: 8px; overflow: hidden; }
        .lib-item img { width: 100%; display: block; }
        .plus-btn { position: absolute; top: 8px; right: 8px; background: var(--mint); color: #000; border: none; border-radius: 50%; width: 28px; height: 28px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 10; font-size: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.8); }
        .plus-btn:hover { background: #fff; transform: scale(1.1); }

        .controls { background: var(--card); border: 1px solid var(--border); border-radius: 15px; padding: 25px; margin-bottom: 30px; }
        .btn-mint { background: var(--mint); color: #000; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; }
        .btn-blue { background: var(--blue); color: #000; border: none; padding: 8px; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 11px; }
        
        .loader { position: fixed; inset: 0; background: rgba(0,0,0,0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
    </style>
</head>
<body>
    <div class="loader" id="loader"><h2 style="color:var(--mint)">NEURAL ENGINE: LOCKING SUBJECTS</h2><p>Applying CTR optimizations...</p></div>

    <div class="sidebar" id="sidebar" style="display:none;">
        <div style="padding: 20px; border-bottom: 1px solid var(--border); font-weight: bold; font-size: 12px; color: var(--mint);">LIVE EXTRACTIONS</div>
        <div class="scroll-area" id="libraryGrid"></div>
        <div class="history-pane">
            <div style="font-size: 10px; color: #8A94A6; margin-bottom: 8px;">PREVIOUS SESSIONS</div>
            <div id="historyGrid"></div>
        </div>
    </div>

    <div class="workspace">
        <div id="authPanel" style="text-align:center; padding-top:100px;">
            <h1>HEATHUMB LAB V13</h1>
            <input type="password" id="passCode" placeholder="Access Code" style="padding:10px; border-radius:5px;">
            <button onclick="checkAuth()" class="btn-mint" style="width:150px; margin-top:10px;">ENTER</button>
        </div>

        <div id="labPanel" style="display:none;">
            <div class="controls">
                <input type="file" id="videoFile" style="margin-bottom:15px; display:block;">
                <button onclick="processVideo()" class="btn-mint">DEEP SCAN VIDEO (CTR+) </button>
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
            
            // Move current to history
            const current = document.getElementById('libraryGrid').innerHTML;
            if(current) document.getElementById('historyGrid').insertAdjacentHTML('afterbegin', current);

            document.getElementById('loader').style.display = 'flex';
            const fd = new FormData();
            fd.append('video', v);

            try {
                const res = await fetch('/process', { method: 'POST', body: fd });
                const data = await res.json();
                
                if(data.status === 'success') {
                    document.getElementById('sidebar').style.display = 'flex';
                    document.getElementById('libraryGrid').innerHTML = data.library.map(u => `
                        <div class="lib-item">
                            <img src="${u}">
                            <button class="plus-btn" onclick="promote('${u}')">+</button>
                        </div>
                    `).join('');
                    
                    document.getElementById('mainGrid').innerHTML = data.pack.map(item => createCard(item.url, item.reason)).join('');
                }
            } catch(e) { alert("Processing Error"); }
            document.getElementById('loader').style.display = 'none';
        }

        function createCard(url, reason) {
            return `
                <div class="img-card">
                    <img src="${url}">
                    <div style="font-size:11px; margin:10px 0; color:#8A94A6;"><b>CTR Analysis:</b> ${reason}</div>
                    <div style="display:flex; gap:10px;">
                        <input type="text" placeholder="Neural Instructions..." style="flex:1; background:#000; border:1px solid var(--border); color:#fff; padding:8px; border-radius:5px;">
                        <button class="btn-blue" onclick="remix(this)">REMIX (0.7)</button>
                        <button class="btn-mint" style="width:70px; font-size:10px;" onclick="window.open('${url}')">SAVE</button>
                    </div>
                </div>`;
        }

        function promote(u) {
            document.getElementById('mainGrid').insertAdjacentHTML('afterbegin', createCard(u, "Manually Promoted Source"));
        }

        async function remix(btn) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            const prompt = card.querySelector('input').value;

            btn.innerText = "Processing...";
            const res = await fetch('/remix', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: img.src, prompt: prompt })
            });
            const d = await res.json();
            if(d.url) img.src = d.url;
            btn.innerText = "REMIX (0.7)";
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

        # 2. Workspace Population (Extreme Low Strength to keep it REAL)
        pack = []
        for i in range(min(6, len(raw_frames))):
            r = fal_client.subscribe("fal-ai/flux-pro", {
                "image_url": raw_frames[i],
                "prompt": "Keep the original image exactly as it is. Add a large, professional, bold text headline overlay. Do not modify the human or the background.",
                "strength": 0.2 # 0.2 Strength means 80% of the original photo stays UNTOUCHED
            })
            pack.append({"url": r['images'][0]['url'], "reason": "Subject-locked with text optimization."})

        s3.delete_object(Bucket=BUCKET, Key=fn)
        return jsonify({"status": "success", "pack": pack, "library": raw_frames})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/remix', methods=['POST'])
def remix():
    d = request.json
    # As requested: using 0.7 strength for manual remixes to allow more AI creativity
    r = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": d['url'],
        "prompt": d['prompt'],
        "strength": 0.7 
    })
    return jsonify({"url": r['images'][0]['url']})

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
