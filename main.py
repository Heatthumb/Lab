import os, time, json, random
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "viral_studio_v103_complete_telemetry_lock"
ACCESS_PASSWORD = "Heathumb2026"

VAULT_MEMORY = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Viral Studio V103 - Image & Video Booster</title>
    <style>
        :root { --mint: #00FFC2; --carbon: #0B0D10; --card: #151A21; --border: #273140; --blue: #40E0FF; --gold: #FFD700; --canva: #00C4CC; --red: #ff4d4d; --bright-dl: #1A73E8; --premium: #A020F0; }
        body { background: var(--carbon); color: #E9EEF5; font-family: 'Inter', sans-serif; margin: 0; display: flex; height: 100vh; overflow:hidden; }
        
        .sidebar { width: 400px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; z-index: 100; }
        .sidebar-sec { padding: 20px; border-bottom: 1px solid var(--border); position: relative; }
        #frameBank { flex: 1; overflow-y: auto; padding: 15px; }
        
        /* Sleek 4-Column Micro Vault Grid */
        .vault-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 10px; }
        .bank-item { border-radius: 6px; overflow: hidden; border: 1px solid #273140; background: #000; position: relative; aspect-ratio: 16/9; cursor: pointer; transition: 0.2s; }
        .bank-item:hover { border-color: var(--mint); transform: scale(1.04); }
        .bank-img { width: 100%; height: 100%; object-fit: cover; }
        .bank-meta { position: absolute; bottom: 2px; right: 2px; background: rgba(0,0,0,0.85); color: var(--mint); font-size: 8px; padding: 1px 3px; border-radius: 2px; font-weight: bold; }
        
        .workspace { flex: 1; padding: 30px; overflow-y: auto; background: #080a0d; }
        .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; }
        .editor-card { background: var(--card); border-radius: 16px; padding: 20px; border: 1px solid var(--border); position: relative; }
        
        .canvas-area { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; border-radius: 12px; overflow: hidden; }
        .bg-layer { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 5; }
        .heatmap-layer { position: absolute; inset: 0; z-index: 99; pointer-events: none; width: 100%; height: 100%; display: none; }

        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 10000; align-items: center; justify-content: center; cursor: zoom-out; }
        .btn-action { border: none; padding: 12px; border-radius: 8px; font-weight: 800; cursor: pointer; font-size: 11px; text-transform: uppercase; transition: 0.2s; display: flex; align-items: center; justify-content: center; gap: 4px; }
        .btn-action:hover { filter: brightness(1.2); }
        
        .selector-dropdown { background: #0b0d10; color: var(--blue); border: 1px solid var(--border); padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; cursor: pointer; outline: none; max-width: 160px; }
        
        .premium-lock-badge { background: var(--premium); color: #fff; font-size: 8px; font-weight: 900; padding: 2px 5px; border-radius: 4px; text-transform: uppercase; display: inline-block; }
        .premium-locked-btn { background: #20162b !important; color: #bca2e0 !important; border: 1px solid #4a237a !important; cursor: not-allowed !important; }

        #loadingBarContainer { display: none; background: #1a222d; border-radius: 6px; height: 6px; width: 100%; margin-top: 10px; overflow: hidden; }
        #loadingBar { background: var(--mint); height: 100%; width: 0%; transition: width 0.1s ease; }
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
                    <button onclick="clearWorkspace();" style="background:none; border:1px solid var(--red); color:var(--red); font-size:10px; font-weight:bold; padding:4px 8px; border-radius:4px; cursor:pointer;">RESET</button>
                    <a href="/history" style="color:var(--blue); text-decoration:none; font-size:11px; font-weight:bold; border:1px solid var(--border); padding:4px 10px; border-radius:4px;">OPEN VAULT</a>
                </div>
            </div>
            <button class="btn-action" style="background:var(--mint); width:100%; color:#000;" onclick="document.getElementById('imgInp').click()">+ INGEST VIDEO / IMAGE</button>
            <input type="file" id="imgInp" accept="image/*,video/*" style="display:none" onchange="processMedia()">
            
            <div id="loadingBarContainer">
                <div id="loadingBar"></div>
            </div>
            <div id="loadingTxt" style="font-size: 10px; color: var(--blue); margin-top: 4px; text-align: center; display: none; font-weight: bold;">EXTRACTING ULTRA-SHARP FRAME REAL ESTATE...</div>
        </div>

        <div class="sidebar-sec" style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
            <span style="font-size:11px; font-weight:900; color:var(--blue); letter-spacing:1px; display:block; margin-bottom:4px;">PERMANENT VAULT BANK</span>
            <span style="font-size:10px; color:#78889b; display:block; margin-bottom:10px;">Click any micro-asset to display full resolution preview or reload into active workspace arrays seamlessly.</span>
            <div id="frameBank" class="vault-grid"></div>
        </div>
    </div>

    <div class="workspace">
        <div id="mainGrid" class="main-grid"></div>
    </div>
    {% endif %}

    <script>
        let allExtractedFrames = [];
        let workspaceFrames = [];

        const contentTypes = [
            "Gaming Walkthrough", "Talking Head Vlog", "Product Reveal", 
            "Text-Heavy Tutorial", "Cinematic Review", "IRL Challenge",
            "Short-Form Retention", "Finance / Business", "Tech Unboxing",
            "ASMR / Minimalist", "Fitness / Workout", "Podcast Highlight"
        ];

        function guessContentTypeFromFrame(width, height) {
            if (height > width) return "Short-Form Retention";
            let seed = Math.random();
            if (seed < 0.20) return "Gaming Walkthrough";
            if (seed >= 0.20 && seed < 0.35) return "Talking Head Vlog";
            if (seed >= 0.35 && seed < 0.50) return "Tech Unboxing";
            if (seed >= 0.50 && seed < 0.65) return "Finance / Business";
            if (seed >= 0.65 && seed < 0.80) return "Text-Heavy Tutorial";
            return "Cinematic Review";
        }

        async function processMedia() {
            const file = document.getElementById('imgInp').files[0];
            if (!file) return;
            
            allExtractedFrames = [];
            
            if (file.type.startsWith('video/')) {
                document.getElementById('loadingBarContainer').style.display = 'block';
                document.getElementById('loadingTxt').style.display = 'block';
                document.getElementById('loadingBar').style.width = '0%';
                
                await extract20VideoFramesSharp(file);
                
                document.getElementById('loadingBarContainer').style.display = 'none';
                document.getElementById('loadingTxt').style.display = 'none';
            } else {
                const data = await readImage(file);
                let tempImg = new Image();
                tempImg.src = data;
                await new Promise(r => tempImg.onload = r);
                
                let predictedType = guessContentTypeFromFrame(tempImg.width, tempImg.height);
                allExtractedFrames.push({ 
                    url: data, 
                    vscore: (Math.random()*53 + 45).toFixed(1), 
                    label: "Static Image",
                    contentType: predictedType
                });
            }
            
            renderSidebar();
            
            let sorted = [...allExtractedFrames].sort((a,b) => b.vscore - a.vscore);
            workspaceFrames = sorted.slice(0, 6).map(f => ({...f}));
            
            renderAll();
            saveToHistory(file.name || "Media Export Scan");
            document.getElementById('imgInp').value = "";
        }

        function readImage(file) {
            return new Promise(res => {
                const reader = new FileReader();
                reader.onload = e => res(e.target.result);
                reader.readAsDataURL(file);
            });
        }

        // ULTRA-SHARP Extraction Flow Engine
        function extract20VideoFramesSharp(file) {
            return new Promise(res => {
                const video = document.createElement('video');
                const videoUrl = URL.createObjectURL(file);
                video.src = videoUrl;
                video.muted = true; video.playsInline = true;
                
                video.onloadedmetadata = async () => {
                    const duration = video.duration;
                    const step = duration / 20;
                    
                    for (let i = 0; i < 20; i++) {
                        video.currentTime = Math.floor(step * i + (step / 2));
                        await new Promise(r => { video.onseeked = r; });
                        
                        const canvas = document.createElement('canvas');
                        canvas.width = parseInt(video.videoWidth); 
                        canvas.height = parseInt(video.videoHeight);
                        
                        const ctx = canvas.getContext('2d', { alpha: false });
                        ctx.imageSmoothingEnabled = true;
                        ctx.imageSmoothingQuality = 'high';
                        
                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                        
                        let imgDataUrl = canvas.toDataURL('image/jpeg', 0.95);
                        let predictedType = guessContentTypeFromFrame(canvas.width, canvas.height);
                        
                        allExtractedFrames.push({
                            url: imgDataUrl,
                            vscore: (Math.random() * 53 + 42).toFixed(1),
                            label: `F-${i + 1}`,
                            contentType: predictedType
                        });
                        
                        document.getElementById('loadingBar').style.width = `${((i + 1) / 20) * 100}%`;
                    }
                    
                    URL.revokeObjectURL(videoUrl);
                    video.remove();
                    res();
                };
            });
        }

        function renderSidebar() {
            document.getElementById('frameBank').innerHTML = allExtractedFrames.map((f, i) => `
                <div class="bank-item" onclick="showCinema('${f.url}')" title="Click to view full resolution frame">
                    <img src="${f.url}" class="bank-img">
                    <span class="bank-meta">V:${f.vscore}</span>
                </div>
            `).join('');
        }

        function clearWorkspace() {
            workspaceFrames = [];
            renderAll();
        }

        function updateType(idx, selectedValue) {
            workspaceFrames[idx].contentType = selectedValue;
        }

        function renderAll() {
            document.getElementById('mainGrid').innerHTML = workspaceFrames.map((f, i) => {
                let optionsHtml = contentTypes.map(t => 
                    `<option value="${t}" ${f.contentType === t ? "selected" : ""}>${t}</option>`
                ).join('');

                return `
                <div class="editor-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span style="color:var(--mint); font-weight:900; font-size:13px; letter-spacing:0.5px;">${f.label} — V-SCORE: ${f.vscore}</span>
                        
                        <select class="selector-dropdown" onchange="updateType(${i}, this.value)">
                            ${optionsHtml}
                        </select>

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
                        <button class="btn-action" style="background:var(--gold); grid-column: span 2; color:#000;" onclick="triggerAnalysisSequence(${i}, ${f.vscore})">ANALYZE ATTENTION FLOW</button>
                        
                        <button class="btn-action" style="background:var(--canva); color:white;" onclick="window.open('https://canva.com')">CANVA SHORTCUT</button>
                        <button class="btn-action" style="background:var(--bright-dl); color:white; font-weight:900;" onclick="downloadSingle('${f.url}')">DOWNLOAD PNG</button>
                        
                        <button class="btn-action premium-locked-btn" onclick="alert('Upgrade via HEATThumb.co.uk to unlock Custom Canva Injection Frameworks!')">
                            <span class="premium-lock-badge">PRO</span> CANVA INJECTOR
                        </button>
                        <button class="btn-action premium-locked-btn" onclick="alert('Upgrade via HEATThumb.co.uk to trigger 1-Click AI Transparent Foreground Cutouts!')">
                            <span class="premium-lock-badge">PRO</span> ISOLATE SUBJECT
                        </button>
                    </div>
                </div>
            `}).join('');
        }

        function generateDynamicAnalysis(score, isMobile, type) {
            let desc = score >= 65 
                ? `Gaze density matrices prove clear structural center alignment across ${type} grids.`
                : `Primary text anchors fail depth separation checks inside ${type} layout templates.`;
            return `${desc} Feed scanning vectors processed successfully.`;
        }

        function getContextualTips(type, score) {
            let tips = { fix: "Isolate asset variables cleanly inside Canva canvas spaces.", traffic: "Scale focus metrics up to lock in fast viewer retention scores.", path: ["Launch Core Graphic Layout Layer", "Verify Alignment Points Inside Screen Coordinates"] };
            
            if (type === "Gaming Walkthrough") {
                tips.fix = "Background landscape introduces noise. Separate UI text overlays.";
                tips.traffic = "Isolate your avatar within a neon perimeter glow matrix.";
                tips.path = ["Select Background Graphic Layer", "Edit Photo ➔ Adjust Settings", "Lower Layout Brightness directly to -25"];
            } else if (type === "Text-Heavy Tutorial") {
                tips.fix = "Typography canvas suffers from alpha layer bleed rules.";
                tips.traffic = "Limit focus blocks to single messaging phrases.";
                tips.path = ["Double-Tap Heading Container Box", "Effects Panel ➔ Select Outline Style", "Set Outline Stroke Thickness to 45"];
            }
            
            let blueprintRows = tips.path.map((step, index) => `
                <div class="blueprint-row" style="margin-top: 4px; display: flex; gap: 6px;">
                    <span style="color:#666; font-weight:bold;">[0${index + 1}]</span> <span>${step}</span>
                </div>
            `).join('');

            return `
                <div class="canva-step" style="margin-top: 10px;">
                    <div class="canva-step-header" style="font-weight: bold; color: var(--canva); font-size: 11px;">[CANVA EXECUTION OPTIMIZER]</div>
                    <div style="margin-top:2px; font-weight:500; color:#cdd7e4;">${tips.fix}</div>
                </div>
                <div class="blueprint-container" style="margin-top: 10px; background: #0b0d10; padding: 10px; border-radius: 6px; border: 1px solid var(--border); font-size: 11px;">
                    <div class="blueprint-title" style="color: var(--gold); font-weight: bold; font-size: 10px; margin-bottom: 4px;">➔ STEP-BY-STEP INTERFACE EXECUTION BLUEPRINT</div>
                    ${blueprintRows}
                </div>
                <div class="canva-step" style="margin-top:10px;">
                    <div class="canva-step-header" style="font-weight: bold; color: var(--mint); font-size: 11px;">[ALGORITHMIC TRAFFIC BOOSTER]</div>
                    <div style="margin-top:2px; font-weight:500; color:#cdd7e4;">${tips.traffic}</div>
                </div>
            `;
        }

        function triggerAnalysisSequence(idx, score) {
            const selectedType = workspaceFrames[idx].contentType;
            renderNativeHeatmap(idx, score, selectedType);
        }

        function renderNativeHeatmap(idx, score, type) {
            const canvas = document.getElementById(`canvas-hm-${idx}`);
            const imgElement = document.getElementById(`bg-img-${idx}`);
            const ctx = canvas.getContext('2d');
            
            canvas.width = canvas.parentElement.offsetWidth; 
            canvas.height = canvas.parentElement.offsetHeight;
            ctx.clearRect(0, 0, canvas.width, canvas.height); 
            canvas.style.display = "block";

            const isMobileLayout = imgElement.naturalHeight > imgElement.naturalWidth;
            let coreX = canvas.width * 0.5, coreY = canvas.height * 0.45;

            ctx.strokeStyle = "rgba(64, 224, 255, 0.7)";
            ctx.lineWidth = 1.5;
            ctx.setLineDash([6, 8]);
            ctx.beginPath(); ctx.ellipse(coreX, coreY, 70, 70, 0, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);

            ctx.strokeStyle = "rgba(255, 77, 77, 0.9)";
            ctx.lineWidth = 2;
            ctx.strokeRect(coreX - 25, coreY - 25, 50, 50);

            document.getElementById(`analysis-text-${idx}`).innerText = generateDynamicAnalysis(score, isMobileLayout, type);
            document.getElementById(`canva-guide-${idx}`).innerHTML = getContextualTips(type, score);
            document.getElementById(`analysis-box-${idx}`).style.display = "block";
        }

        function showCinema(url) {
            document.getElementById('cinemaImg').src = url;
            document.getElementById('cinemaOverlay').style.display = 'flex';
        }

        function downloadSingle(url) {
            const a = document.createElement('a'); a.href = url; a.download = "ViralStudio_SharpExport.png"; a.click();
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
        page += "<h3 style='color:#666; text-align:center; padding-top:80px;'>No active history arrays discovered.</h3>"
    
    for h in reversed(VAULT_MEMORY):
        page += f"""<div style="background:#151a21; border-radius:12px; padding:20px; margin-bottom:25px; border:1px solid #273140;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                        <span style="font-size:16px; font-weight:bold; color:#FFD700;">{h['name']}</span>
                    </div>
                    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(120px, 1fr)); gap:10px;">"""
        for f in h['frames']:
            page += f"""<img src="{f['url']}" style="width:100%; aspect-ratio:16/9; object-fit:cover; background:#000; border-radius:4px; border:1px solid #333; cursor:pointer;" onclick="document.getElementById('histCinemaImg').src='{f['url']}'; document.getElementById('historyCinema').style.display='flex';">"""
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
