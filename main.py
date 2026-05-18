import os, boto3, fal_client, time, threading
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "studio_v81_final_logic"
ACCESS_PASSWORD = "Heathumb2026"

# Cloud Config
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/heatmap.js/2.0.2/heatmap.min.js"></script>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --gold: #FFD700; --canva: #00C4CC; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow:hidden; }
        .sidebar { width: 340px; background: var(--card); border-right: 1px solid var(--border); overflow-y: auto; }
        .sidebar-sec { padding: 20px; border-bottom: 1px solid var(--border); }
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; max-width: 1400px; margin: 0 auto; }
        .editor-card { background: var(--card); border-radius: 16px; padding: 20px; border: 1px solid var(--border); position: relative; }
        
        /* THE STAGE */
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; overflow: hidden; border-radius: 12px; }
        .bg-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 1; image-rendering: -webkit-optimize-contrast; }
        
        /* FIX: Heatmap now has absolute dimensions inside the relative parent */
        .heatmap-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5; pointer-events: none; }

        .card-controls { margin-top: 20px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .ai-gen-btn { grid-column: span 2; background: var(--gold); color: #000; border: none; padding: 14px; border-radius: 8px; font-weight: 900; cursor: pointer; }
        .canva-btn { grid-column: span 2; background: var(--canva); color: #fff; border: none; padding: 12px; border-radius: 8px; font-weight: 800; cursor: pointer; }
        .c-btn { background: #242b35; border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 6px; cursor: pointer; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div style="display:flex; height:100vh; width:100vw; align-items:center; justify-content:center;">
        <form method="POST" action="/login">
            <input type="password" name="password" style="padding:12px; border-radius:8px;">
            <button type="submit">LOGIN</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-sec">
            <button class="ai-gen-btn" style="background:var(--mint)" onclick="document.getElementById('vidInp').click()">LOAD 4K SOURCE</button>
            <input type="file" id="vidInp" style="display:none" onchange="processVideo()">
        </div>
        <div id="statusMsg" style="padding:10px; color:var(--blue); font-size:12px; text-align:center;"></div>
    </div>
    <div class="workspace">
        <div id="mainGrid" class="main-grid"></div>
    </div>
    <video id="h-vid" style="display:none"></video>
    {% endif %}

    <script>
        let workspaceFrames = [];
        let heatmapInstances = {};

        async function processVideo() {
            const file = document.getElementById('vidInp').files[0];
            const video = document.getElementById('h-vid');
            video.src = URL.createObjectURL(file);
            document.getElementById('statusMsg').innerText = "Extracting RAW 4K Frames...";

            video.onloadedmetadata = async () => {
                workspaceFrames = []; // Clear old
                // FIX: Loop for 6 images instead of 2
                const spots = [0.1, 0.25, 0.4, 0.6, 0.75, 0.9];
                for(let i=0; i < spots.length; i++) {
                    const data = await grab(video, video.duration * spots[i]);
                    workspaceFrames.push({ url: data, showHeat: false, id: i });
                }
                document.getElementById('statusMsg').innerText = "6 Frames Ready.";
                renderAll();
            };
        }

        async function grab(v, t) {
            return new Promise(res => {
                v.currentTime = t;
                v.onseeked = () => {
                    const c = document.createElement('canvas');
                    // FIX: Force native 4K resolution
                    c.width = v.videoWidth; c.height = v.videoHeight;
                    const ctx = c.getContext('2d');
                    ctx.drawImage(v, 0, 0);
                    res(c.toDataURL('image/png', 1.0));
                };
            });
        }

        function renderAll() {
            const grid = document.getElementById('mainGrid');
            grid.innerHTML = workspaceFrames.map((f, i) => `
                <div class="editor-card">
                    <div class="canvas-area" id="area-${i}">
                        <img src="${f.url}" class="bg-layer">
                        <div id="hm-layer-${i}" class="heatmap-layer"></div>
                    </div>
                    <div class="card-controls">
                        <button class="ai-gen-btn" onclick="initHeatmap(${i})">ANALYZE ATTENTION (A/B)</button>
                        <button class="canva-btn" onclick="toCanva(${i})">SEND TO CANVA</button>
                    </div>
                </div>
            `).join('');
        }

        // FIX: Re-written Heatmap Logic
        function initHeatmap(idx) {
            const container = document.getElementById(`hm-layer-${idx}`);
            // Reset container
            container.innerHTML = ''; 
            
            const hmap = h337.create({
                container: container,
                radius: 50,
                maxOpacity: .6,
                blur: .8
            });

            // Random points for demo - in production, this is your AI data
            const points = [
                { x: container.offsetWidth / 2, y: container.offsetHeight / 3, value: 100 },
                { x: container.offsetWidth / 1.5, y: container.offsetHeight / 2, value: 50 }
            ];

            hmap.setData({ max: 100, data: points });
        }

        function toCanva(idx) {
            alert("Syncing 4K Frame to your Canva account...");
            window.open("https://www.canva.com/", "_blank");
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD: session['logged_in'] = True
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
