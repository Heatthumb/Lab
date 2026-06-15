import os
import time
import json
import random
import base64
import sys
import subprocess

# Auto-provision core dependencies (No complex AI binaries required)
required_packages = ["opencv-python-headless", "numpy", "Flask"]
missing_packages = []

for pkg in required_packages:
    try:
        if pkg == "opencv-python-headless":
            import cv2
        else:
            __import__(pkg)
    except ImportError:
        missing_packages.append(pkg)

if missing_packages:
    print(f"Provisioning stable processing stack: {missing_packages}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)

import cv2
import numpy as np
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "viral_studio_v103_autobooster_core"
ACCESS_PASSWORD = "Heathumb2026"

VAULT_MEMORY = []

# Fetch the native internal front-facing tracking matrix from OpenCV's source build maps
HAAR_FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viral Studio V103 - AI Auto-Booster Platform</title>
    <style>
        :root {
            --mint: #00FFC2;
            --carbon: #0B0D10;
            --card: #151A21;
            --border: #273140;
            --blue: #40E0FF;
            --gold: #FFD700;
            --red: #ff4d4d;
            --canva: #00C4CC;
            --purple-ai: #8A2BE2;
            --text-main: #E9EEF5;
            --text-muted: #7A8B9E;
        }

        body {
            background: var(--carbon);
            color: var(--text-main);
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
            letter-spacing: -0.2px;
        }

        .sidebar {
            width: 400px;
            background: var(--card);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            z-index: 100;
            box-shadow: 10px 0 30px rgba(0,0,0,0.5);
        }

        .sidebar-header {
            padding: 25px 20px;
            border-bottom: 1px solid var(--border);
            background: rgba(11, 13, 16, 0.4);
        }

        .sidebar-title {
            font-size: 16px;
            font-weight: 900;
            color: #ffffff;
            margin: 0 0 5px 0;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .sidebar-subtitle {
            font-size: 11px;
            color: var(--text-muted);
            margin: 0;
        }

        .sidebar-controls {
            padding: 20px;
            border-bottom: 1px solid var(--border);
        }

        #frameBank {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: rgba(0,0,0,0.15);
        }

        .bank-item {
            border-radius: 12px;
            border: 1px solid var(--border);
            background: #000000;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
            transition: all 0.25s ease;
        }

        .bank-item:hover {
            transform: translateY(-2px);
            border-color: var(--blue);
            box-shadow: 0 5px 15px rgba(64, 224, 255, 0.15);
        }

        .bank-meta {
            display: block;
            padding: 8px 12px;
            background: rgba(21, 26, 33, 0.85);
            font-size: 10px;
            font-weight: 700;
            color: var(--text-main);
            border-bottom: 1px solid var(--border);
            letter-spacing: 0.5px;
        }

        .bank-img {
            width: 100%;
            aspect-ratio: 16/9;
            object-fit: contain;
            cursor: pointer;
            display: block;
            background: #050505;
        }

        .workspace {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            background: #080a0d;
            position: relative;
        }

        .workspace-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border);
        }

        .main-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
        }

        @media (max-width: 1400px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }

        .editor-card {
            background: var(--card);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid var(--border);
            box-shadow: 0 15px 35px rgba(0,0,0,0.4);
            position: relative;
        }

        .canvas-container-box {
            position: relative;
            background: #000000;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.05);
            aspect-ratio: 16/9;
            margin-top: 10px;
        }

        .comparison-img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
        }

        .selector-dropdown {
            background: #0b0d10;
            color: #ffffff;
            border: 1px solid var(--border);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            outline: none;
        }

        .btn-action {
            border: none;
            padding: 14px 20px;
            border-radius: 10px;
            font-weight: 800;
            cursor: pointer;
            font-size: 11px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .btn-action:hover {
            filter: brightness(1.1);
            transform: translateY(-1px);
        }

        .loader-bar-wrap {
            width: 100%;
            height: 6px;
            background: #1a1f26;
            border-radius: 3px;
            margin-top: 15px;
            overflow: hidden;
            display: none;
        }

        .loader-bar-fill {
            height: 100%;
            width: 100%;
            background: linear-gradient(90deg, var(--blue), var(--mint));
        }

        .overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(5, 7, 10, 0.95);
            z-index: 10000;
            align-items: center;
            justify-content: center;
            cursor: zoom-out;
        }

        .gate-wrapper {
            display: flex;
            height: 100vh;
            width: 100vw;
            align-items: center;
            justify-content: center;
            background: var(--carbon);
        }

        .gate-card {
            background: var(--card);
            padding: 40px;
            border-radius: 24px;
            border: 1px solid var(--border);
            width: 360px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.6);
            text-align: center;
        }
    </style>
</head>
<body>

    <div id="cinemaOverlay" class="overlay" onclick="this.style.display='none'">
        <img id="cinemaImg" src="" style="max-width:92%; max-height:92%; border:2px solid #333; border-radius:12px; box-shadow:0 25px 60px rgba(0,0,0,0.8);">
    </div>

    {% if not session.get('logged_in') %}
    <div class="gate-wrapper">
        <form method="POST" action="/login" class="gate-card">
            <div style="width:50px; height:50px; background:rgba(0, 255, 194, 0.1); border-radius:12px; display:flex; align-items:center; justify-content:center; margin:0 auto 20px auto; border:1px solid var(--mint);">
                <span style="color:var(--mint); font-weight:900; font-size:20px;">V</span>
            </div>
            <h2 style="color:#ffffff; margin:0 0 8px 0; font-weight:900; font-size:20px; letter-spacing:0.5px;">VIRAL STUDIO CORE</h2>
            <p style="color:var(--text-muted); font-size:12px; margin:0 0 25px 0;">Multi-System Intelligent Extraction Build 1.03</p>
            
            <input type="password" name="password" placeholder="ENTER ACCESS KEY" required autocomplete="off"
                   style="width:100%; box-sizing:border-box; padding:14px; margin-bottom:20px; background:#0b0d10; color:white; border:1px solid var(--border); border-radius:8px; text-align:center; font-weight:bold; letter-spacing:2px; font-size:12px; outline:none;">
            
            <button type="submit" class="btn-action" style="background:var(--mint); color:#0b0d10; width:100%; font-weight:900;">INITIALIZE SESSION</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-header">
            <h1 class="sidebar-title">Viral Studio</h1>
            <p class="sidebar-subtitle">Multi-System Aesthetic Engine v1.03 // Active</p>
        </div>
        <div class="sidebar-controls">
            <button class="btn-action" style="background:var(--mint); color:#050505; width:100%; font-weight:900;" onclick="document.getElementById('imgInp').click()">
                + INGEST SOURCE MEDIA
            </button>
            <input type="file" id="imgInp" accept="image/*,video/*" style="display:none" onchange="uploadAndProcessMedia()">
            
            <div class="loader-bar-wrap" id="loadingBar">
                <div class="loader-bar-fill" id="progress"></div>
            </div>
        </div>
        <div id="frameBank"></div>
    </div>

    <div class="workspace">
        <div class="workspace-header">
            <div>
                <h2 style="margin:0; font-weight:900; font-size:22px; color:#fff;">WORKSPACE OVERVIEW</h2>
                <p style="margin:5px 0 0 0; font-size:12px; color:var(--text-muted);">Programmatic extraction funnel displaying elite thumbnail candidates</p>
            </div>
            <div style="display:flex; gap:12px;">
                <a href="/history" style="text-decoration:none;" class="btn-action" style="background:transparent; border:1px solid var(--border); color:var(--text-main);">VIEW HISTORIC VAULT</a>
                <button class="btn-action" style="background:var(--red); color:white;" onclick="clearWorkspace()">CLEAR GRID</button>
            </div>
        </div>
        <div id="mainGrid" class="main-grid"></div>
    </div>
    {% endif %}

    <script>
        let allExtractedFrames = [];
        let workspaceFrames = [];
        let userVideoUploadCount = 0; 
        
        const contentTypes = [
            "Gaming Walkthrough", "Talking Head Vlog", "Product Reveal", 
            "Text-Heavy Tutorial", "Cinematic Review", "IRL Challenge", 
            "Short-Form Retention", "Finance / Business", "Tech Unboxing"
        ];

        async function uploadAndProcessMedia() {
            const file = document.getElementById('imgInp').files[0];
            if (!file) return;

            const loadingBar = document.getElementById('loadingBar');
            if(loadingBar) loadingBar.style.display = 'block';

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/ingest', {
                    method: 'POST',
                    body: formData
                });
                const resData = await response.json();
                
                if (resData.status === 'success') {
                    allExtractedFrames = resData.all_candidates;
                    workspaceFrames = resData.top_6_picks;
                    userVideoUploadCount = resData.upload_count;
                    
                    renderSidebar();
                    renderAll();
                } else {
                    alert("Error processing media pipeline: " + resData.msg);
                }
            } catch (e) {
                console.error(e);
                alert("Server execution pipeline connection failure.");
            } finally {
                if(loadingBar) loadingBar.style.display = 'none';
            }
        }

        function renderSidebar() {
            const bank = document.getElementById('frameBank');
            if(!bank) return;
            
            if (allExtractedFrames.length === 0) {
                bank.innerHTML = `
                    <div style="padding:20px 10px; text-align:center;">
                        <p style="color:var(--text-muted); font-size:12px; margin-bottom:15px;">No video elements ingested yet.</p>
                        <div style="background:rgba(0, 255, 194, 0.03); border:1px dashed var(--border); border-radius:12px; padding:12px; font-size:11px; text-align:left; color:#b5c4d6; line-height:1.4;">
                            🛡️ <b>Multi-System Funnel Rules:</b><br>
                            • Discards blur & motion sweeps<br>
                            • Scores composition metrics via native cascades<br>
                            • Displays candidate pool inside sidebar<br>
                        </div>
                    </div>`;
                return;
            }

            let usageBanner = `
                <div style="background:#1a1f26; border:1px solid var(--border); padding:10px; border-radius:8px; margin-bottom:15px; font-size:11px;">
                    <div style="display:flex; justify-content:between; margin-bottom:4px;">
                        <span style="color:var(--text-muted);">Session Audited Ingests:</span>
                        <b style="color:#fff; margin-left:auto;">${userVideoUploadCount} Videos Processed</b>
                    </div>
                </div>
                <h3 style="font-size:11px; font-weight:900; color:var(--text-muted); text-transform:uppercase; margin:0 0 10px 0; letter-spacing:0.5px;">Filtered Candidate Pool</h3>
            `;

            let itemsHtml = allExtractedFrames.map((f, i) => {
                return `
                    <div class="bank-item">
                        <span class="bank-meta" style="display:flex; justify-content:space-between;">
                            <span>${f.label} (Score: ${parseFloat(f.vscore).toFixed(1)})</span>
                        </span>
                        <img src="${f.originalUrl}" class="bank-img" onclick="showCinema('${f.originalUrl}')">
                        <div style="padding:10px;">
                            <button class="btn-action" style="background:transparent; border:1px solid var(--border); color:var(--text-main); width:100%; font-size:10px; padding:6px;" onclick="addAlternativeFrameToWorkspace(${i})">
                                + ADD TO WORKSPACE STAGE
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            bank.innerHTML = usageBanner + itemsHtml;
        }

        function addAlternativeFrameToWorkspace(index) {
            const selected = allExtractedFrames[index];
            workspaceFrames.push({
                ...selected,
                id: 'ws_custom_' + Date.now() + '_' + Math.random().toString(36).substr(2,3),
                label: `➕ LAYER: ${selected.label}`
            });
            renderAll();
        }

        function updateType(idx, selectedValue) {
            workspaceFrames[idx].contentType = selectedValue;
        }

        function clearWorkspace() {
            workspaceFrames = [];
            renderAll();
        }

        function renderAll() {
            const grid = document.getElementById('mainGrid');
            if(!grid) return;

            if (workspaceFrames.length === 0) {
                grid.innerHTML = `<div style="grid-column:span 2; padding:60px 20px; text-align:center; border:2px dashed var(--border); border-radius:16px; color:var(--text-muted);">WORKSPACE COMPOSITION STAGE VACANT</div>`;
                return;
            }

            grid.innerHTML = workspaceFrames.map((f, i) => {
                let optionsHtml = contentTypes.map(t => 
                    `<option value="${t}" ${f.contentType === t ? "selected" : ""}>${t}</option>`
                ).join('');

                return `
                <div class="editor-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                        <span style="color:var(--mint); font-weight:900; font-size:12px; letter-spacing:0.5px;">
                            ${f.label}
                        </span>
                        
                        <div style="display:flex; gap:10px; align-items:center;">
                            <select class="selector-dropdown" onchange="updateType(${i}, this.value)">
                                ${optionsHtml}
                            </select>
                            <button onclick="workspaceFrames.splice(${i},1); renderAll();" style="color:var(--red); background:none; border:none; cursor:pointer; font-weight:bold; font-size:16px; outline:none;">✕</button>
                        </div>
                    </div>

                    <div class="canvas-container-box" id="canvas-wrap-${i}">
                        <img src="${f.currentUrl}" class="comparison-img" id="bg-img-${i}" onclick="showCinema('${f.currentUrl}')">
                    </div>

                    <div style="margin-top:15px; display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                        <button id="boost-btn-${i}" class="btn-action" style="background:var(--purple-ai); color:white; grid-column: span 2;" onclick="executeAIAutoBoost(${i})">✨ RUN AI AUTO-BOOSTER</button>
                        <button class="btn-action" style="background:var(--canva); color:white; grid-column: span 2;" onclick="window.open('https://canva.com')">EXPORT LAYOUT TO CANVA</button>
                    </div>
                </div>
            `}).join('');
        }

        async function executeAIAutoBoost(idx) {
            const frame = workspaceFrames[idx];
            const btn = document.getElementById(`boost-btn-${idx}`);
            if(btn) {
                btn.innerText = "PROCESSING MATRIX...";
                btn.style.opacity = "0.6";
                btn.disabled = true;
            }

            try {
                const response = await fetch('/api/boost', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ image: frame.currentUrl })
                });
                const resData = await response.json();
                
                if(resData.status === 'success') {
                    frame.currentUrl = resData.boosted_image;
                    renderAll();
                    setTimeout(() => {
                        alert(`✨ AI BOOSTER MATRIX ENGAGED\\n\\nBackground exposure attenuation (-18%) successfully computed via server OpenCV pipelines.\\nRadial subject focus masks applied completely to native assets.`);
                    }, 50);
                } else {
                    alert("Booster communication fault.");
                }
            } catch(e) {
                console.error(e);
                alert("Server processing exception encountered.");
            }
        }

        function showCinema(url) {
            document.getElementById('cinemaImg').src = url;
            document.getElementById('cinemaOverlay').style.display = 'flex';
        }
    </script>
</body>
</html>
"""

VIDEO_UPLOAD_COUNT = 0

@app.route('/api/ingest', methods=['POST'])
def api_ingest():
    global VIDEO_UPLOAD_COUNT
    if 'file' not in request.files:
        return jsonify({"status": "error", "msg": "Missing file binary asset"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "msg": "Empty filename space"}), 400

    temp_path = os.path.join("/tmp" if os.name != 'nt' else "C:\\Windows\\Temp", file.filename)
    file.save(temp_path)
    
    try:
        cap = cv2.VideoCapture(temp_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        
        all_candidates = []
        last_hist = None
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Coarse sample filter loop: inspect 2 frames per second to reduce CPU workload
            if frame_idx % int(fps / 2) == 0:
                h, w, _ = frame.shape
                
                # System 1: Scene Cut Evaluation via Color Histogram shifts
                hist = cv2.calcHist([frame], [0, 1, 2], None, [4, 4, 4], [0, 256, 0, 256, 0, 256])
                cv2.normalize(hist, hist)
                
                is_scene_change = True
                if last_hist is not None:
                    similarity = cv2.compareHist(hist, last_hist, cv2.HISTCMP_CORREL)
                    if similarity > 0.75:
                        is_scene_change = False
                        
                if is_scene_change or frame_idx == 0:
                    last_hist = hist
                    
                    # System 2: Technical validation (Blur checking via Laplacian variance)
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
                    
                    if blur_score >= 65.0: 
                        
                        # System 3 & 4: Stable Native Haar Matrix Assessment (Replaces problematic MediaPipe)
                        faces = HAAR_FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(40, 40))
                        
                        aesthetic_score = 40.0
                        
                        if len(faces) > 0:
                            # Pull the largest face structure detected in the viewport loop
                            largest_face = max(faces, key=lambda f: f[2] * f[3])
                            fx, fy, fw, fh = largest_face
                            
                            # Measure how close the subject is relative to powerful center rule framing rules
                            cx = (fx + (fw / 2)) / w
                            cy = (fy + (fh / 2)) / h
                            composition_bonus = 1.0 - (abs(cx - 0.5) + abs(cy - 0.45))
                            
                            # Formulate an integrated score value based on image contrast stability and placement values
                            contrast_factor = min(np.std(gray) / 1.5, 45.0)
                            aesthetic_score = 45.0 + contrast_factor + (composition_bonus * 20)
                        else:
                            # Scenic/Text asset handling balance score mechanics
                            aesthetic_score = float(np.clip(blur_score / 5.5, 35.0, 80.0))

                        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                        b64_data = base64.b64encode(buffer).decode('utf-8')
                        data_url = f"data:image/jpeg;base64,{b64_data}"
                        
                        all_candidates.append({
                            "id": f"frame_{int(time.time())}_{frame_idx}",
                            "url": data_url,
                            "originalUrl": data_url,
                            "currentUrl": data_url,
                            "vscore": aesthetic_score,
                            "label": f"Scene Candidate ({(frame_idx/fps):.1f}s)",
                            "contentType": "Talking Head Vlog"
                        })
                        
            frame_idx += 1
            
        cap.release()
        try:
            os.remove(temp_path)
        except:
            pass

        if not all_candidates:
            return jsonify({"status": "error", "msg": "No frames cleared technical quality checks."}), 400

        all_candidates.sort(key=lambda x: x['vscore'], reverse=True)
        
        top_6_raw = all_candidates[:6]
        top_6_picks = []
        for item in top_6_raw:
            top_6_picks.append({
                **item,
                "id": f"ws_auto_{random.randint(100,999)}",
                "label": f"✨ AUTO-PICK: {item['label']}"
            })
            
        VIDEO_UPLOAD_COUNT += 1
        
        VAULT_MEMORY.append({
            'id': str(random.randint(100000, 999999)),
            'name': file.filename, 
            'date': time.strftime("%Y-%m-%d %H:%M"), 
            'frames': [{"id": f['id'], "label": f['label'], "url": f['url']} for f in all_candidates[:12]]
        })

        return jsonify({
            "status": "success",
            "all_candidates": all_candidates,
            "top_6_picks": top_6_picks,
            "upload_count": VIDEO_UPLOAD_COUNT
        })
        
    except Exception as e:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/api/boost', methods=['POST'])
def boost_api():
    try:
        data = request.json
        img_str = data['image']
        
        header, encoded = img_str.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        h, w, c = img.shape

        invGamma = 1.0 / 0.82
        lut_table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        bg_muted = cv2.LUT(img, lut_table)

        mask = np.zeros((h, w), dtype=np.uint8)
        center_x, center_y = int(w * 0.5), int(h * 0.45)
        radius = int(min(w, h) * 0.4)
        
        cv2.circle(mask, (center_x, center_y), radius, 255, -1)
        mask_blur = cv2.GaussianBlur(mask, (101, 101), 0) / 255.0
        mask_blur = cv2.merge([mask_blur, mask_blur, mask_blur])

        subject_boosted = cv2.convertScaleAbs(img, alpha=1.12, beta=8)
        final_canvas = (subject_boosted * mask_blur + bg_muted * (1.0 - mask_blur)).astype(np.uint8)

        _, buffer = cv2.imencode('.jpg', final_canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        encoded_output = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            "status": "success",
            "boosted_image": f"data:image/jpeg;base64,{encoded_output}"
        })
    except Exception as err:
        return jsonify({"status": "error", "msg": str(err)}), 400

@app.route('/history')
def history_page():
    if not session.get('logged_in'): return redirect(url_for('home'))
    
    page = """<body style="background:#0b0d10; color:white; font-family:sans-serif; padding:40px;">
              <div id="historyCinema" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.95); z-index:99999; align-items:center; justify-content:center; cursor:zoom-out;" onclick="this.style.display='none'">
                  <img id="histCinemaImg" src="" style="max-width:92%; max-height:92%; object-fit:contain; border:2px solid #555; border-radius:6px;">
              </div>

              <div style="max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; align-items:center;">
              <h1 style="color:#00FFC2; font-size:28px; margin:0;">VAULT INDEX</h1>
              <div style="display:flex; gap:12px;">
                  <a href="/" style="color:#40E0FF; text-decoration:none; border:1px solid #273140; padding:10px 20px; border-radius:8px; font-weight:bold;">RETURN TO WORKSPACE</a>
              </div>
              </div><br><hr style="border:0; border-top:1px solid #273140; margin:20px 0;">"""
    
    if not VAULT_MEMORY: 
        page += "<h3 style='color:#666; text-align:center; padding-top:80px;'>No active history discovered.</h3>"
    
    for h in reversed(VAULT_MEMORY):
        page += f"""<div style="background:#151a21; border-radius:12px; padding:20px; margin-bottom:25px; border:1px solid #273140;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                        <span style="font-size:16px; font-weight:bold; color:#FFD700;">{h['name']} <span style="color:#666; font-size:11px; margin-left:10px;">(Top 12 Extracted Elements Saved)</span></span>
                        <span style="color:#666; font-size:12px;">{h['date']}</span>
                    </div>
                    
                    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); gap:12px; margin-top:10px;">"""
        
        for f in h['frames']:
            page += f"""<div style="position:relative; background:#000; border-radius:6px; overflow:hidden; border:1px solid #333;">
                        <img src="{f['url']}" style="width:100%; display:block; aspect-ratio:16/9; object-fit:contain; cursor:pointer;" onclick="document.getElementById('histCinemaImg').src='{f['url']}'; document.getElementById('historyCinema').style.display='flex';">
                        <div style="padding:4px; display:grid; grid-template-columns:1fr; background:#1a1f26;">
                            <a href="{f['url']}" download style="background:#1A73E8; text-decoration:none; color:white; font-size:9px; padding:4px; text-align:center; font-weight:bold; border-radius:2px;">DOWNLOAD IMAGE</a>
                        </div></div>"""
        page += "</div></div>"
    return page + "</body>"

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ACCESS_PASSWORD: 
        session['logged_in'] = True
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
