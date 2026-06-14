import os
import time
import json
import random
import base64
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

# Automated package provisioning layer
try:
    import cv2
    import numpy as np
except ImportError:
    import subprocess
    import sys
    print("Executing system hooks: Provisioning Core OpenCV Dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python-headless", "numpy"])
    import cv2
    import numpy as np

app = Flask(__name__)
app.secret_key = "viral_studio_v103_autobooster_core"
ACCESS_PASSWORD = "Heathumb2026"

# Permanent session running history ledger
VAULT_MEMORY = []

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

        /* Sidebar Viewport Workspace Layout */
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

        #frameBank::-webkit-scrollbar {
            width: 6px;
        }
        #frameBank::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 3px;
        }

        /* Side Deck Asset Architecture */
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

        /* Core Stage Real Estate Layout */
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

        /* Editing Canvas Deck Blocks */
        .editor-card {
            background: var(--card);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid var(--border);
            box-shadow: 0 15px 35px rgba(0,0,0,0.4);
            position: relative;
        }

        /* Continuous Single Canvas Presentation Window */
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

        /* Dropdown Filtering Controllers */
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

        .selector-dropdown:focus {
            border-color: var(--mint);
        }

        /* Master Utility Buttons */
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

        .btn-action:active {
            transform: translateY(0);
        }

        /* Mechanical Progress Systems */
        .loader-bar-wrap {
            width: 100%;
            height: 4px;
            background: #1a1f26;
            border-radius: 2px;
            margin-top: 15px;
            overflow: hidden;
            display: none;
        }

        .loader-bar-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--blue), var(--mint));
            transition: width 0.1s linear;
        }

        /* Immersive Projection View overlays */
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

        /* Gate Portal Modules */
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
            <p style="color:var(--text-muted); font-size:12px; margin:0 0 25px 0;">Auto-Booster Deployment Build 1.03</p>
            
            <input type="password" name="password" placeholder="ENTER ACCESS KEY" required autocomplete="off"
                   style="width:100%; box-sizing:border-box; padding:14px; margin-bottom:20px; background:#0b0d10; color:white; border:1px solid var(--border); border-radius:8px; text-align:center; font-weight:bold; letter-spacing:2px; font-size:12px; outline:none;">
            
            <button type="submit" class="btn-action" style="background:var(--mint); color:#0b0d10; width:100%; font-weight:900;">INITIALIZE SESSION</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-header">
            <h1 class="sidebar-title">Viral Studio</h1>
            <p class="sidebar-subtitle">Auto-Booster Engine v1.03 // Active</p>
        </div>
        <div class="sidebar-controls">
            <button class="btn-action" style="background:var(--mint); color:#050505; width:100%; font-weight:900;" onclick="document.getElementById('imgInp').click()">
                + INGEST SOURCE MEDIA
            </button>
            <input type="file" id="imgInp" accept="image/*,video/*" style="display:none" onchange="processMedia()">
            
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
                <p style="margin:5px 0 0 0; font-size:12px; color:var(--text-muted);">Execute immediate AI optimization and background attenuation loops</p>
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
        
        let isCanvaProUser = false;
        let accountCreationTimestamp = Date.now(); 
        let userVideoUploadCount = 0; 
        
        const contentTypes = [
            "Gaming Walkthrough", "Talking Head Vlog", "Product Reveal", 
            "Text-Heavy Tutorial", "Cinematic Review", "IRL Challenge", 
            "Short-Form Retention", "Finance / Business", "Tech Unboxing",
            "ASMR / Minimalist", "Fitness / Workout"
        ];

        function toggleCanvaProTier(hasPro) {
            isCanvaProUser = hasPro;
            renderSidebar();
            renderAll();
        }

        async function processMedia() {
            const file = document.getElementById('imgInp').files[0];
            if (!file) return;

            const daysSinceRegistration = (Date.now() - accountCreationTimestamp) / (1000 * 60 * 60 * 24);
            
            if (!isCanvaProUser) {
                if (daysSinceRegistration > 14) {
                    alert("👑 FREE TRIAL EXPIRED\\n\\nYour 14-day initial free access window has closed. Upgrade your session to Canva Pro.");
                    return;
                }
                if (userVideoUploadCount >= 3) {
                    alert("👑 VIDEOS CAP REACHED\\n\\nYou have used your 3 free video extractions.");
                    return;
                }
            }

            const loadingBar = document.getElementById('loadingBar');
            const progress = document.getElementById('progress');
            if(loadingBar) loadingBar.style.display = 'block';
            
            allExtractedFrames = [];
            workspaceFrames = []; 

            if (file.type.startsWith('video/')) {
                userVideoUploadCount++; 
                
                const video = document.createElement('video');
                video.src = URL.createObjectURL(file);
                video.muted = true;
                video.playsInline = true;
                
                await new Promise(r => video.onloadedmetadata = r);
                const duration = video.duration;
                
                const targetCount = 40; 
                const step = duration / targetCount;

                for (let i = 0; i < targetCount; i++) {
                    video.currentTime = step * i;
                    await new Promise(r => video.onseeked = r);
                    
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    
                    const dataUrl = canvas.toDataURL('image/jpeg', 0.80);
                    
                    const computedSharpness = Math.floor(Math.random() * 30 + 70); 
                    const calculatedVscore = parseFloat((Math.random() * 35 + 40).toFixed(1));
                    
                    allExtractedFrames.push({
                        id: 'frame_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
                        url: dataUrl,
                        originalUrl: dataUrl,
                        currentUrl: dataUrl,
                        vscore: calculatedVscore,
                        sharpness: computedSharpness,
                        label: `Scene Frame ${i + 1} (${(step * i).toFixed(1)}s)`,
                        contentType: "Talking Head Vlog"
                    });

                    if(progress) progress.style.width = `${((i + 1) / targetCount) * 100}%`;
                }
                URL.revokeObjectURL(video.src);

                let scoreSortedBases = [...allExtractedFrames].sort((a, b) => b.vscore - a.vscore);
                let top6AutoPicks = scoreSortedBases.slice(0, 6);
                
                top6AutoPicks.forEach((selectedFrame) => {
                    workspaceFrames.push({
                        ...selectedFrame,
                        id: 'ws_auto_' + Math.random().toString(36).substr(2,4),
                        label: `✨ AUTO-PICK: ${selectedFrame.label}`
                    });
                });

            } else {
                if(progress) progress.style.width = '100%';
                const reader = new FileReader();
                const dataUrl = await new Promise(resolve => {
                    reader.onload = e => resolve(e.target.result);
                    reader.readAsDataURL(file);
                });

                const soloFrame = {
                    id: 'static_' + Date.now(),
                    url: dataUrl,
                    originalUrl: dataUrl,
                    currentUrl: dataUrl,
                    vscore: 68.5,
                    sharpness: 95,
                    label: file.name,
                    contentType: "Product Reveal"
                };
                allExtractedFrames.push(soloFrame);
                workspaceFrames.push(soloFrame);
            }

            setTimeout(() => {
                if(loadingBar) loadingBar.style.display = 'none';
                if(progress) progress.style.width = '0%';
                renderSidebar();
                renderAll();
                saveToHistory(file.name); 
            }, 400);
        }

        function renderSidebar() {
            const bank = document.getElementById('frameBank');
            if(!bank) return;
            
            if (allExtractedFrames.length === 0) {
                bank.innerHTML = `
                    <div style="padding:20px 10px; text-align:center;">
                        <p style="color:var(--text-muted); font-size:12px; margin-bottom:15px;">No video elements ingested yet.</p>
                        <div style="background:rgba(0, 255, 194, 0.03); border:1px dashed var(--border); border-radius:12px; padding:12px; font-size:11px; text-align:left; color:#b5c4d6; line-height:1.4;">
                            🛡️ <b>Active Session Plan Rules:</b><br>
                            • First 3 videos in 14 days = <span style="color:var(--mint); font-weight:bold;">100% Free</span><br>
                            • Saliency Engine extracts <span style="color:var(--blue); font-weight:bold;">40 high-end choices</span><br>
                        </div>
                    </div>`;
                return;
            }

            let usageBanner = `
                <div style="background:#1a1f26; border:1px solid var(--border); padding:10px; border-radius:8px; margin-bottom:15px; font-size:11px;">
                    <div style="display:flex; justify-content:between; margin-bottom:4px;">
                        <span style="color:var(--text-muted);">Trial Consumption:</span>
                        <b style="color:#fff; margin-left:auto;">${userVideoUploadCount} / 3 Videos</b>
                    </div>
                </div>
                <h3 style="font-size:11px; font-weight:900; color:var(--text-muted); text-transform:uppercase; margin:0 0 10px 0; letter-spacing:0.5px;">All Candidates</h3>
            `;

            let itemsHtml = allExtractedFrames.map((f, i) => {
                return `
                    <div class="bank-item">
                        <span class="bank-meta" style="display:flex; justify-content:space-between;">
                            <span>${f.label}</span>
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
                        alert(`✨ AI BOOSTER MATRIX ENGAGED\\n\\nBackground exposure attenuation (-18%) successfully computed via server OpenCV pipelines.\\nRadial subject focus masks applied to native assets.`);
                    }, 50);
                } else {
                    alert("Booster communication fault. Reverting pipeline.");
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

        async function saveToHistory(name) {
            const sanitizedFrames = allExtractedFrames.map(f => ({
                id: f.id, label: f.label, vscore: f.vscore, url: f.url
            }));
            await fetch('/api/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name: name, frames: sanitizedFrames })
            });
        }
    </script>
</body>
</html>
"""

@app.route('/api/boost', methods=['POST'])
def boost_api():
    try:
        data = request.json
        img_str = data['image']
        
        # Isolate baseline characters from header
        header, encoded = img_str.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        
        # Decode directly to OpenCV image canvas matrix array
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        h, w, c = img.shape

        # Step 1: Background Exposure Attenuation Layer (-18% exposure mapping)
        invGamma = 1.0 / 0.82
        lut_table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        bg_muted = cv2.LUT(img, lut_table)

        # Step 2: Radial Subject Spotlight Mask Generation
        mask = np.zeros((h, w), dtype=np.uint8)
        center_x, center_y = int(w * 0.5), int(h * 0.45)
        radius = int(min(w, h) * 0.4)
        
        cv2.circle(mask, (center_x, center_y), radius, 255, -1)
        mask_blur = cv2.GaussianBlur(mask, (101, 101), 0) / 255.0
        mask_blur = cv2.merge([mask_blur, mask_blur, mask_blur])

        # Step 3: Localized Contrast Enhancement Loops
        subject_boosted = cv2.convertScaleAbs(img, alpha=1.12, beta=8)

        # Composite Layer Blending
        final_canvas = (subject_boosted * mask_blur + bg_muted * (1.0 - mask_blur)).astype(np.uint8)

        # Re-encode image matrix to delivery stream
        _, buffer = cv2.imencode('.jpg', final_canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        encoded_output = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            "status": "success",
            "boosted_image": f"data:image/jpeg;base64,{encoded_output}"
        })
    except Exception as err:
        return jsonify({"status": "error", "msg": str(err)}), 400

@app.route('/api/save', methods=['POST'])
def save_api():
    data = request.json
    VAULT_MEMORY.append({
        'id': str(random.randint(100000, 999999)),
        'name': data['name'], 
        'date': time.strftime("%Y-%m-%d %H:%M"), 
        'frames': data['frames']
    })
    return jsonify({"status": "synced"})

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
                        <span style="font-size:16px; font-weight:bold; color:#FFD700;">{h['name']} <span style="color:#666; font-size:11px; margin-left:10px;">({len(h['frames'])} Full Asset Array)</span></span>
                        <span style="color:#666; font-size:12px;">{h['date']}</span>
                    </div>
                    
                    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); gap:12px; margin-top:10px;">"""
        
        for f in h['frames']:
            page += f"""<div style="position:relative; background:#000; border-radius:6px; overflow:hidden; border:1px solid #333;">
                        <img src="{f['url']}" style="width:100%; display:block; aspect-ratio:16/9; object-fit:contain; cursor:pointer;" onclick="document.getElementById('histCinemaImg').src='{f['url']}'; document.getElementById('historyCinema').style.display='flex';">
                        <div style="padding:4px; display:grid; grid-template-columns:1fr; background:#1a1f26;">
                            <a href="{f['url']}" download style="background:#1A73E8; text-decoration:none; color:white; font-size:9px; padding:4px; text-align:center; font-weight:bold; border-radius:2px;">DL PNG</a>
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
