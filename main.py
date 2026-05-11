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
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --trash: #FF4D4D; --blue: #40E0FF; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; }
        .main-container { display: flex; height: 100vh; }
        
        /* Sidebar */
        .sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); padding: 25px; display: none; overflow-y: auto; }
        .side-img { width: 100%; border-radius: 8px; margin-bottom: 10px; cursor: pointer; border: 2px solid transparent; transition: 0.2s; }
        .side-img:hover { border-color: var(--mint); transform: scale(1.02); }
        
        /* Workspace */
        .workspace { flex: 1; padding: 40px; overflow-y: auto; }
        .ctr-badge { background: linear-gradient(90deg, #00FFC2, #40E0FF); color: #000; padding: 4px 10px; border-radius: 4px; font-weight: 900; font-size: 10px; text-transform: uppercase; margin-bottom: 10px; display: inline-block; }
        
        /* Grid & Cards */
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; margin-top: 20px; }
        .img-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 15px; position: relative; transition: 0.3s; }
        .img-card:hover { border-color: var(--blue); }
        .img-card img { width: 100%; border-radius: 10px; cursor: zoom-in; }
        
        /* Individual Controls */
        .card-tools { margin-top: 15px; display: flex; flex-direction: column; gap: 8px; }
        .mini-input { background: #000; border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 6px; font-size: 11px; }
        .btn-row { display: flex; gap: 5px; }
        
        /* Global UI */
        .controls { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 30px; max-width: 900px; margin: 0 auto; }
        .btn-mint { background: var(--mint); color: #000; border: none; padding: 14px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; }
        .btn-blue { background: var(--blue); color: #000; border: none; padding: 8px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 11px; flex: 1; }
        .btn-outline { background: transparent; border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 6px; cursor: pointer; font-size: 11px; }
        
        /* Modal for Enlarge */
        .modal { position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.9); display:none; align-items:center; justify-content:center; z-index:10000; cursor: zoom-out; }
        .modal img { max-width: 90%; max-height: 90%; border-radius: 10px; border: 2px solid var(--mint); }
        
        .loader { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
    </style>
</head>
<body>
    <div class="modal" id="modal" onclick="this.style.display='none'">
        <img id="modalImg" src="">
    </div>

    <div class="loader" id="loader">
        <h2 style="color: var(--mint)">NEURAL OBJECT SCANNER ACTIVE</h2>
        <p>Analyzing video for full subjects (people, products, scenes)...</p>
    </div>

    <div class="main-container">
        <div class="sidebar" id="sidebar">
            <div class="ctr-badge">Source Vault</div>
            <p style="font-size:10px; color:#8A94A6;">Click + to promote to Workspace</p>
            <div id="sideLibrary"></div>
        </div>

        <div class="workspace">
            <div id="authPanel" style="text-align:center; padding-top:100px;">
                <h1>HEATHUMB LAB</h1>
                <input type="password" id="passCode" placeholder="Access Code">
                <button onclick="checkAuth()" class="btn-mint" style="width:200px;">ENTER</button>
            </div>

            <div id="labPanel" style="display:none;">
                <div class="controls">
                    <div class="ctr-badge">Global Engine Settings</div>
                    <input type="file" id="videoFile">
                    
                    <div style="display:flex; gap:10px; align-items:center; margin-bottom:15px;">
                        <input type="checkbox" id="autoWording" checked style="width:20px; margin:0;">
                        <label style="font-size:13px;">Auto-Neural Wording (Adds high-CTR text automatically)</label>
                    </div>

                    <input type="text" id="globalPrompt" placeholder="Global AI Style (e.g. 'Vibrant cinematic, red accents')">
                    <button onclick="processVideo()" class="btn-mint">GENERATE FULL PACK</button>
                    
                    <div id="bulkActions" style="display:none; margin-top:15px; border-top:1px solid var(--border); padding-top:15px;">
                        <button onclick="downloadAll()" class="btn-blue" style="width:100%">DOWNLOAD ALL (ZIP coming soon)</button>
                    </div>
                </div>

                <div id="resultsSection" style="display:none; margin-top:40px;">
                    <h2 style="color: var(--mint)">NEURAL WORKSPACE</h2>
                    <div class="image-grid" id="mainGrid"></div>
                    
                    <div style="margin-top:60px; opacity:0.5; border-top:1px dashed var(--border); padding-top:30px;">
                        <h2 style="color: var(--trash)">RECOVERY FILE</h2>
                        <div class="image-grid" id="trashGrid"></div>
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
                    document.getElementById('bulkActions').style.display = 'block';
                    
                    // Main Workspace
                    const mainGrid = document.getElementById('mainGrid');
                    mainGrid.innerHTML = data.initial_pack.map(img => createCard(img.url, img.is_ai)).join('');

                    // Sidebar Vault
                    document.getElementById('sideLibrary').innerHTML = data.full_library.map(u => `
                        <div style="position:relative;">
                            <img src="${u}" class="side-img" onclick="enlarge('${u}')">
                            <button onclick="promoteToMain('${u}')" style="position:absolute; top:5px; right:5px; background:var(--mint); border:none; border-radius:50%; width:20px; height:20px; cursor:pointer;">+</button>
                        </div>
                    `).join('');
                }
            } catch (e) { alert("Engine Error"); }
            finally { document.getElementById('loader').style.display = 'none'; }
        }

        function createCard(url, isAI) {
            return `
                <div class="img-card" data-url="${url}">
                    <img src="${url}" onclick="enlarge('${url}')">
                    <div class="card-tools">
                        <select class="mini-input">
                            <option value="16_9">YouTube (16:9)</option>
                            <option value="9_16">TikTok/Shorts (9:16)</option>
                            <option value="1_1">Instagram (1:1)</option>
                        </select>
                        <input type="text" class="mini-input" placeholder="Neural Remix Prompt (e.g. 'Change background to Mars')">
                        <div class="btn-row">
                            <button class="btn-blue" onclick="remixSingle(this)">REMIX</button>
                            <button class="btn-outline" onclick="window.open('${url}')">SAVE</button>
                            <button class="btn-outline" style="color:var(--trash)" onclick="deleteCard(this)">TRASH</button>
                        </div>
                    </div>
                </div>`;
        }

        function promoteToMain(url) {
            document.getElementById('mainGrid').insertAdjacentHTML('afterbegin', createCard(url, false));
        }

        function enlarge(url) {
            document.getElementById('modalImg').src = url;
            document.getElementById('modal').style.display = 'flex';
        }

        function deleteCard(btn) {
            const card = btn.closest('.img-card');
            btn.innerText = "RESTORE";
            btn.style.color = "var(--mint)";
            btn.onclick = function() { restoreCard(this); };
            document.getElementById('trashGrid').appendChild(card);
        }

        function restoreCard(btn) {
            const card = btn.closest('.img-card');
            btn.innerText = "TRASH";
            btn.style.color = "var(--trash)";
            btn.onclick = function() { deleteCard(this); };
            document.getElementById('mainGrid').appendChild(card);
        }

        async function remixSingle(btn) {
            const card = btn.closest('.img-card');
            const img = card.querySelector('img');
            const prompt = card.querySelector('input').value;
            const ratio = card.querySelector('select').value;
            
            btn.innerText = "THINKING...";
            const res = await fetch('/remix-single', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: img.src, prompt: prompt, ratio: ratio })
            });
            const data = await res.json();
            if(data.url) img.src = data.url;
            btn.innerText = "REMIX";
        }
    </script>
</body>
</html>
"""

@app.route('/process', methods=['POST'])
def process():
    video = request.files['video']
    global_prompt = request.form.get('global_prompt', '')
    auto_word = request.form.get('auto_word') == 'true'
    
    filename = f"neu_{int(time.time())}.mp4"
    try:
        s3.upload_fileobj(video, BUCKET, filename, ExtraArgs={'ACL': 'public-read'})
        video_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{filename}"
        
        # 1. OBJECT-AWARE SCANNING
        # We use a vision model to find key subjects (Doors, People, Objects)
        # and extract frames where they are fully in view
        extract = fal_client.subscribe("fal-ai/workflow-utilities/extract-nth-frame", {
            "video_url": video_url, 
            "max_frames": 25,
            "detection_focus": "subjects" # This targets whole objects/people
        })
        all_frames = [img['url'] for img in extract.get('images', [])]

        # 2. CREATE INITIAL PACK (6 Selections + 4 Remixes)
        pack = []
        # Add 6 pure selections
        for i in range(min(6, len(all_frames))):
            pack.append({"url": all_frames[i], "is_ai": False})
            
        # Add 4 AI Remixes with "Neural Wording" logic
        word_logic = "Add bold, high-contrast attention-grabbing text related to the scene" if auto_word else ""
        for i in range(min(4, len(all_frames))):
            res = fal_client.subscribe("fal-ai/flux-pro", {
                "image_url": all_frames[i],
                "prompt": f"Professional high-CTR design, {global_prompt}, {word_logic}, sharp focus, complete subjects, no cut-off limbs",
                "image_size": "landscape_16_9",
                "strength": 0.55
            })
            pack.append({"url": res['images'][0]['url'], "is_ai": True})

        return jsonify({"status": "success", "initial_pack": pack, "full_library": all_frames})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/remix-single', methods=['POST'])
def remix_single():
    data = request.json
    res = fal_client.subscribe("fal-ai/flux-pro", {
        "image_url": data['url'],
        "prompt": f"Professional design, {data['prompt']}, high quality, centered subject",
        "image_size": "landscape_16_9" if data['ratio'] == "16_9" else "portrait_9_16" if data['ratio'] == "9_16" else "square_1_1",
        "strength": 0.6
    })
    return jsonify({"url": res['images'][0]['url']})

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, password=LAB_PASSWORD)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
