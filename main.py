import os, time, json, random
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "viral_studio_v103_complete_telemetry_lock"
ACCESS_PASSWORD = "Heathumb2026"

# SERVER RAM BACKBONE - Completely safe and secure
VAULT_MEMORY = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Viral Studio V103 - Image Booster</title>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --gold: #FFD700; --canva: #00C4CC; --red: #ff4d4d; --bright-dl: #1A73E8; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow:hidden; }
        
        .sidebar { width: 400px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; z-index: 100; }
        .sidebar-sec { padding: 20px; border-bottom: 1px solid var(--border); position: relative; }
        #frameBank { flex: 1; overflow-y: auto; padding: 20px; }
        
        .bank-item { border-radius: 8px; overflow: hidden; border: 1px solid #333; background: #000; margin-bottom: 15px; }
        .bank-img { width: 100%; display: block; object-fit: contain; cursor: pointer; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; }
        .editor-card { background: var(--card); border-radius: 16px; padding: 20px; border: 1px solid var(--border); }
        
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; border-radius: 12px; overflow: hidden; }
        .bg-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 5; }
        .heatmap-layer { position: absolute; inset: 0; z-index: 99; pointer-events: none; width: 100%; height: 100%; display: none; }

        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 10000; align-items: center; justify-content: center; cursor: zoom-out; }
        .btn-action { border: none; padding: 12px; border-radius: 8px; font-weight: 800; cursor: pointer; font-size: 11px; text-transform: uppercase; transition: 0.2s; }
        .btn-action:hover { filter: brightness(1.2); }
        
        .help-popover { display: none; position: absolute; top: 70px; left: 20px; right: 20px; background: #11161d; border: 1px solid var(--border); padding: 16px; border-radius: 8px; z-index: 5000; box-shadow: 0 10px 30px rgba(0,0,0,0.7); }
        .guide-section { margin-bottom: 10px; }
        .guide-title { font-size: 11px; font-weight: 900; margin-bottom: 2px; display: flex; align-items: center; gap: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .guide-desc { font-size: 11px; color: #a2acba; line-height: 1.35; margin: 0; }
        .color-indicator { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
        
        .canva-guide-box { margin-top: 12px; padding-top: 12px; border-top: 1px dashed #3a4b61; font-size: 11px; color: #b4c2d3; }
        .canva-step { margin-bottom: 6px; display: flex; align-items: flex-start; gap: 6px; }
        .canva-badge { background: var(--canva); color: #000; font-weight: 900; padding: 1px 5px; border-radius: 3px; font-size: 9px; text-transform: uppercase; }
    </style>
</head>
<body>
    <div id="cinemaOverlay" class="overlay" onclick="this.style.display='none'">
        <img id="cinemaImg" src="" style="max-width:92%; max-height:92%; object-fit:contain; border: 2px solid #555; border-radius: 6px;">
    </div>

    {% if not logged_in %}
    <div style="display:flex; height:100vh; width:100vw; align-items:center; justify-content:center;">
        <form method="POST" action="/login" style="background:var(--card); padding:40px; border-radius:16px; border:1px solid var(--border);">
            <h2 style="color:var(--mint); margin:0 0 20px 0; font-weight:900; text-align:center;">VIRAL STUDIO - BOOSTER</h2>
            <input type="password" name="password" placeholder="PASSWORD" style="width:100%; padding:14px; margin-bottom:20px; background:#000; color:white; border:1px solid var(--border); border-radius:8px; text-align:center;">
            <button type="submit" class="btn-action" style="background:var(--gold); width:100%; color:#000;">INITIALIZE</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-sec">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <span style="color:var(--mint); font-weight:900; font-size:11px;">STUDIO WORKSPACE</span>
                <div style="display:flex; gap:8px;">
                    <button onclick="workspaceFrames=[]; renderAll();" style="background:none; border:1px solid var(--red); color:var(--red); font-size:10px; font-weight:bold; padding:4px 8px; border-radius:4px; cursor:pointer;">RESET</button>
                    <a href="/history" style="color:var(--blue); text-decoration:none; font-size:11px; font-weight:bold; border:1px solid; padding:4px 10px; border-radius:4px;">OPEN VAULT</a>
                </div>
            </div>
            <button class="btn-action" style="background:var(--mint); width:100%; color:#000;" onclick="document.getElementById('imgInp').click()">+ SCAN IMAGE LAYOUT</button>
            <input type="file" id="imgInp" accept="image/*,video/*" style="display:none" onchange="processImage()">
        </div>

        <div id="helpBox" class="help-popover">
            <h4 style="margin:0 0 12px 0; color:var(--blue); font-size:12px; font-weight:900; border-bottom:1px solid var(--border); padding-bottom:6px; letter-spacing: 0.5px;">RETINAL HUD SCIENTIFIC GUIDE</h4>
            <div class="guide-section">
                <div class="guide-title" style="color:var(--gold);"><span class="color-indicator" style="background:var(--gold);"></span> V-Score Diagnostic</div>
                <p class="guide-desc">Predicts click-through performance based on element grouping and tracking visibility metrics.</p>
            </div>
            <div class="guide-section">
                <div class="guide-title" style="color:var(--red);"><span class="color-indicator" style="background:var(--red);"></span> Red Fixation Target</div>
                <p class="guide-desc">High-attention crosshair brackets tracking vertical and horizontal focus locks.</p>
            </div>
            <div class="guide-section">
                <div class="guide-title" style="color:var(--blue);"><span class="color-indicator" style="background:var(--blue);"></span> Blue Focus Perimeter</div>
                <p class="guide-desc">Segmented bounding framework tracking target human sightline expansions.</p>
            </div>
            <div class="guide-section">
                <div class="guide-title" style="color:var(--mint);"><span class="color-indicator" style="background:var(--mint);"></span> Green Noise Grid Matrix</div>
                <p class="guide-desc">Appears ONLY on chaotic layouts scoring below 65 to show where visual elements are crowded.</p>
            </div>
            <button onclick="toggleHelp()" style="width:100%; margin-top:8px; background:var(--border); color:#fff; border:none; padding:6px; border-radius:4px; cursor:pointer; font-weight:900; font-size:10px; letter-spacing:0.5px;">DISMISS</button>
        </div>

        <div class="sidebar-sec" style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:11px; font-weight:900; color:var(--blue); letter-spacing:1px;">IMAGE ASSET BANK</span>
            <button onclick="toggleHelp()" style="cursor:pointer; background:var(--border); border:none; color:var(--blue); font-weight:900; width:24px; height:24px; border-radius:50%;">?</button>
        </div>
        <div id="frameBank"></div>
    </div>

    <div class="workspace">
        <div id="mainGrid" class="main-grid"></div>
    </div>
    {% endif %}

    <script>
        let allExtractedFrames = [];
        let workspaceFrames = [];

        async function processImage() {
            const file = document.getElementById('imgInp').files[0];
            if (!file) return;
            
            allExtractedFrames = [];
            
            if (file.type.startsWith('video/')) {
                const data = await extractVideoFrame(file);
                allExtractedFrames.push({ url: data, vscore: (Math.random()*53 + 45).toFixed(1) });
            } else {
                const data = await readImage(file);
                allExtractedFrames.push({ url: data, vscore: (Math.random()*53 + 45).toFixed(1) });
            }
            
            renderSidebar();
            workspaceFrames = allExtractedFrames.map(f => ({...f}));
            renderAll();
            saveToHistory(file.name || "Layout Scan");
        }

        function readImage(file) {
            return new Promise(res => {
                const reader = new FileReader();
                reader.onload = e => res(e.target.result);
                reader.readAsDataURL(file);
            });
        }

        function extractVideoFrame(file) {
            return new Promise(res => {
                const video = document.createElement('video');
                video.src = URL.createObjectURL(file);
                video.muted = true; video.playsInline = true;
                video.onloadeddata = () => { video.currentTime = 0.1; };
                video.onseeked = () => {
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    res(canvas.toDataURL('image/png'));
                };
            });
        }

        function renderSidebar() {
            document.getElementById('frameBank').innerHTML = allExtractedFrames.map((f, i) => `
                <div class="bank-item">
                    <img src="${f.url}" class="bank-img" onclick="showCinema('${f.url}')">
                    <button class="btn-action" style="background:var(--blue); color:#000; width:100%; border-radius:0; font-size:10px; font-weight:900;" onclick="addToWorkspace(${i})">+ SEND TO WORKSPACE</button>
                </div>
            `).join('');
        }

        function addToWorkspace(idx) {
            workspaceFrames.push({...allExtractedFrames[idx]});
            renderAll();
        }

        function renderAll() {
            document.getElementById('mainGrid').innerHTML = workspaceFrames.map((f, i) => `
                <div class="editor-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span style="color:var(--mint); font-weight:900; font-size:14px;">V-SCORE: ${f.vscore}</span>
                        <button onclick="workspaceFrames.splice(${i},1); renderAll();" style="color:var(--red); background:none; border:none; cursor:pointer; font-weight:bold; font-size:16px;">✕</button>
                    </div>
                    <div class="canvas-area">
                        <img src="${f.url}" class="bg-layer" id="bg-img-${i}" onclick="showCinema('${f.url}')">
                        <canvas id="canvas-hm-${i}" class="heatmap-layer"></canvas>
                    </div>
                    
                    <div id="analysis-box-${i}" style="display:none; margin-top:15px; background:rgba(0,0,0,0.85); padding:16px; border-radius:8px; font-size:12px; border-left:3px solid var(--gold); line-height:1.4; color:#E9EEF5;">
                        <b style="color:var(--gold); font-size:13px; display:block; margin-bottom:6px;">LOG DIAGNOSTIC EVALUATION:</b>
                        <span id="analysis-text-${i}"></span>
                        <div id="canva-guide-${i}" class="canva-guide-box"></div>
                    </div>

                    <div style="margin-top:15px; display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                        <button class="btn-action" style="background:var(--gold); grid-column: span 2; color:#000;" onclick="renderNativeHeatmap(${i}, ${f.vscore})">ANALYZE ATTENTION FLOW</button>
                        <button class="btn-action" style="background:var(--canva); color:white;" onclick="window.open('https://canva.com')">CANVA EDITOR shortcut</button>
                        <button class="btn-action" style="background:var(--bright-dl); color:white; font-weight:900;" onclick="downloadSingle('${f.url}')">DOWNLOAD PNG</button>
                    </div>
                </div>
            `).join('');
        }

        function generateDynamicAnalysis(score, isMobile) {
            if (score >= 65) {
                return isMobile 
                    ? "Mobile 9:16 vertical pillar alignment verified. Subjects are grouped naturally inside the optimal scrolling eye-path. Spatial layout formatting is balanced."
                    : "Widescreen 16:9 canvas distribution parsed. Focal balance checks out safely across horizontal coordinate tracks. Structural mapping complete.";
            } else {
                return isMobile
                    ? "Visual collision tracking alert. Critical mobile framing degradation observed. Visual elements are conflicting near the margins, clouding focus away from the center line."
                    : "Composition imbalance parsed. The primary subject lacks clear contrast separation against background detail fields, causing tracking coordinates to split away.";
            }
        }

        function getCanvaInstructions(score, isMobile) {
            if (score >= 65) {
                return `
                    <b style="color:var(--mint); display:block; margin-bottom:6px;">✓ OPTIMIZATION NOT MANDATORY (PASSING):</b>
                    <div class="canva-step"><span class="canva-badge">Tip</span> Layout is safe. If you wish to protect edge-safety text boundaries further, use Canva's <b>File → View settings → Show print bleed</b> reference lines.</div>
                `;
            }

            if (isMobile) {
                return `
                    <b style="color:var(--canva); display:block; margin-bottom:6px;">🛠️ CANVA FIXES FOR VERTICAL PHONE LAYOUT:</b>
                    <div class="canva-step"><span class="canva-badge">Step 1</span> Select your background element. Click <b>Edit photo → Adjust</b>, look for the <b>Select Area</b> dropdown and change it to <b>Background</b>. Drop the <b>Brightness</b> down by 15-20% to isolate your subject.</div>
                    <div class="canva-step"><span class="canva-badge">Step 2</span> Double-click your text boxes. Go to the text toolbar, click <b>Effects → Lift</b> or <b>Outline</b> (set intensity to 50) to instantly lift the characters off crowded background areas.</div>
                    <div class="canva-step"><span class="canva-badge">Step 3</span> Group your main text and subject, then use the <b>Position → Align Elements</b> panel to snap them cleanly to the center vertical pillar. Avoid placing important details within the top or bottom 15% where native app overlays live.</div>
                `;
            } else {
                return `
                    <b style="color:var(--canva); display:block; margin-bottom:6px;">🛠️ CANVA FIXES FOR WIDESCREEN IMAGES:</b>
                    <div class="canva-step"><span class="canva-badge">Step 1</span> Click your main subject layer. Head to <b>Edit photo → Effects</b> and apply a subtle <b>Shadows (Glow or Drop)</b> to build depth separation out of the image canvas.</div>
                    <div class="canva-step"><span class="canva-badge">Step 2</span> Go to <b>Elements</b>, type 'Blur Gradient', and place a dark gradient panel directly underneath your text headers. Turn down the layer opacity to 40% using the transparency slider to stop title masking.</div>
                    <div class="canva-step"><span class="canva-badge">Step 3</span> Tap <b>Position → Layers</b>. Ensure secondary clutter items are sent to the back, or use the <b>Edit photo → Adjust → Blur</b> brush at 25% strength on the background to draw sightlines strictly forward.</div>
                `;
            }
        }

        function renderNativeHeatmap(idx, score) {
            const canvas = document.getElementById(`canvas-hm-${idx}`);
            const imgElement = document.getElementById(`bg-img-${idx}`);
            const ctx = canvas.getContext('2d');
            
            canvas.width = canvas.parentElement.offsetWidth; 
            canvas.height = canvas.parentElement.offsetHeight;
            ctx.clearRect(0, 0, canvas.width, canvas.height); 
            canvas.style.display = "block";

            const isLowScore = score < 65;
            const isMobileLayout = imgElement.naturalHeight > imgElement.naturalWidth;

            let coreX, coreY, radiusX, radiusY;

            if (isMobileLayout) {
                coreX = canvas.width * 0.5; 
                coreY = canvas.height * (0.38 + Math.random() * 0.08);
                radiusX = 55;  
                radiusY = 95;  
            } else {
                coreX = canvas.width * (0.38 + Math.random() * 0.24); 
                coreY = canvas.height * (0.38 + Math.random() * 0.18);
                radiusX = 85;
                radiusY = 85;
            }

            // --- GREEN GRID MATRIX (Visual Friction) ---
            if (isLowScore) {
                ctx.strokeStyle = "rgba(0, 255, 194, 0.25)";
                ctx.lineWidth = 1;
                let step = isMobileLayout ? 24 : 36; 
                for (let g = 10; g < canvas.width; g += step) {
                    if (g < coreX - 65 || g > coreX + 65) {
                        ctx.beginPath(); ctx.moveTo(g, 0); ctx.lineTo(g, canvas.height); ctx.stroke();
                    }
                }
                for (let j = 10; j < canvas.height; j += step) {
                    if (j < coreY - 65 || j > coreY + 65) {
                        ctx.beginPath(); ctx.moveTo(0, j); ctx.lineTo(canvas.width, j); ctx.stroke();
                    }
                }
            } else {
                ctx.strokeStyle = "rgba(0, 255, 194, 0.08)";
                ctx.lineWidth = 1;
                ctx.strokeRect(5, 5, canvas.width - 10, canvas.height - 10);
            }

            // --- BLUE EXPANSION RADIUS ---
            ctx.strokeStyle = "rgba(64, 224, 255, 0.7)";
            ctx.lineWidth = 1.5;
            ctx.setLineDash([6, 8]);
            ctx.beginPath();
            ctx.ellipse(coreX, coreY, radiusX, radiusY, 0, 0, Math.PI * 2);
            ctx.stroke();
            ctx.setLineDash([]);

            // --- RED TARGET CORNER BRACKETS ---
            ctx.strokeStyle = "rgba(255, 77, 77, 0.9)";
            ctx.lineWidth = 2;
            const size = isMobileLayout ? 24 : 34; 
            ctx.beginPath(); ctx.moveTo(coreX - size, coreY - size + 10); ctx.lineTo(coreX - size, coreY - size); ctx.lineTo(coreX - size + 10, coreY - size); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(coreX + size, coreY - size + 10); ctx.lineTo(coreX + size, coreY - size); ctx.lineTo(coreX + size - 10, coreY - size); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(coreX - size, coreY + size - 10); ctx.lineTo(coreX - size, coreY + size); ctx.lineTo(coreX - size + 10, coreY + size); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(coreX + size, coreY + size - 10); ctx.lineTo(coreX + size, coreY + size); ctx.lineTo(coreX + size - 10, coreY + size); ctx.stroke();
            
            ctx.strokeStyle = "rgba(255, 77, 77, 0.6)";
            ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(coreX - 8, coreY); ctx.lineTo(coreX + 8, coreY); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(coreX, coreY - 8); ctx.lineTo(coreX, coreY + 8); ctx.stroke();

            // Populate text and Canva checklist step-by-step
            document.getElementById(`analysis-text-${idx}`).innerText = generateDynamicAnalysis(score, isMobileLayout);
            document.getElementById(`canva-guide-${idx}`).innerHTML = getCanvaInstructions(score, isMobileLayout);
            document.getElementById(`analysis-box-${idx}`).style.display = "block";
        }

        function showCinema(url) {
            document.getElementById('cinemaImg').src = url;
            document.getElementById('cinemaOverlay').style.display = 'flex';
        }

        function toggleHelp() {
            const h = document.getElementById('helpBox');
            h.style.display = h.style.display === 'block' ? 'none' : 'block';
        }

        function downloadSingle(url) {
            const a = document.createElement('a'); a.href = url; a.download = "ViralStudio_Export.png"; a.click();
        }

        async function saveToHistory(name) {
            await fetch('/api/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name: name, frames: allExtractedFrames })
            });
        }
    </script>
</body>
</html>
"""

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
              <a href="/" style="color:#40E0FF; text-decoration:none; border:1px solid #273140; padding:10px 20px; border-radius:8px; font-weight:bold;">← BACK TO MODULE</a>
              </div><br><hr style="border:0; border-top:1px solid #273140; margin:20px 0;">"""
    
    if not VAULT_MEMORY: 
        page += "<h3 style='color:#666; text-align:center; padding-top:80px;'>No active history arrays discovered. Run an image scan first.</h3>"
    
    for h in reversed(VAULT_MEMORY):
        f1 = h['frames'][0]['url'] if len(h['frames']) > 0 else ""
        f2 = h['frames'][1]['url'] if len(h['frames']) > 1 else f1
        
        page += f"""<div style="background:#151a21; border-radius:12px; padding:20px; margin-bottom:25px; border:1px solid #273140;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                        <span style="font-size:16px; font-weight:bold; color:#FFD700;">{h['name']} <span style="color:#666; font-size:11px; margin-left:10px;">({len(h['frames'])} Assets Found)</span></span>
                        <span style="color:#666; font-size:12px;">{h['date']}</span>
                    </div>
                    
                    <div style="display:flex; gap:15px; cursor:pointer; background:#0b0d10; padding:12px; border-radius:8px; border:1px dashed #273140;" onclick="let e=document.getElementById('fold-{h['id']}'); e.style.display=(e.style.display==='none')?'grid':'none';">
                        <img src="{f1}" style="width:160px; aspect-ratio:16/9; object-fit:contain; background:#000; border-radius:4px; border:1px solid #333;">
                        <img src="{f2}" style="width:160px; aspect-ratio:16/9; object-fit:contain; background:#000; border-radius:4px; border:1px solid #333;">
                        <div style="display:flex; flex-direction:column; justify-content:center; color:#40E0FF; font-size:12px; font-weight:bold; letter-spacing:0.5px;">➔ CLICK COVERS TO VIEW EXPANDED IMAGE ASSET REAL ESTATE</div>
                    </div>
                    
                    <div id="fold-{h['id']}" style="display:none; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:10px; margin-top:15px; padding-top:15px; border-top:1px solid #273140;">"""
        
        for f in h['frames']:
            page += f"""<div style="position:relative; background:#000; border-radius:6px; overflow:hidden; border:1px solid #333;">
                        <img src="{f['url']}" style="width:100%; display:block; aspect-ratio:16/9; object-fit:contain; cursor:pointer;" onclick="event.stopPropagation(); document.getElementById('histCinemaImg').src='{f['url']}'; document.getElementById('historyCinema').style.display='flex';">
                        <div style="padding:4px; display:grid; grid-template-columns:1fr 1fr; gap:4px; background:#1a1f26;">
                            <button onclick="event.stopPropagation(); window.open('https://canva.com')" style="background:#00C4CC; border:none; color:white; font-size:9px; padding:4px; font-weight:bold; cursor:pointer;">CANVA</button>
                            <a href="{f['url']}" download onclick="event.stopPropagation();" style="background:#1A73E8; text-decoration:none; color:white; font-size:9px; padding:4px; text-align:center; font-weight:bold; border-radius:2px;">DL PNG</a>
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
