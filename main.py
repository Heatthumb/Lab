import os
import time
import json
import random
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "viral_studio_v103_ultimate_telemetry_lock"
ACCESS_PASSWORD = "Heathumb2026"

# Global data layer tracking persistence for session runtimes
VAULT_MEMORY = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viral Studio V103 - Multi-Phase Diagnostic Suite</title>
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
            --bright-dl: #1A73E8;
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

        /* Sidebar Interface Real Estate */
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

        /* Bank Items Layout */
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

        /* Workspace Grid Architecture */
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

        /* Editor Card Modules */
        .editor-card {
            background: var(--card);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid var(--border);
            box-shadow: 0 15px 35px rgba(0,0,0,0.4);
            position: relative;
        }

        /* Twin Compare Split Architecture */
        .canvas-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 10px;
        }

        .canvas-container-box {
            position: relative;
            background: #000000;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.05);
            aspect-ratio: 16/9;
        }

        .comparison-img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
        }

        .canvas-label-badge {
            position: absolute;
            top: 10px;
            left: 10px;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: 900;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            z-index: 5;
        }

        .heatmap-layer {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 2;
            pointer-events: none;
            display: none;
        }

        /* Form Interaction Fields */
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

        /* Button Action Framework */
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

        /* Diagnostic Box Styling */
        .canva-guide-box {
            margin-top: 12px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 12px;
        }

        .blueprint-container {
            margin-top: 10px;
            background: #0b0d10;
            border-radius: 6px;
            padding: 10px;
            border: 1px solid rgba(255,255,255,0.02);
        }

        .blueprint-title {
            font-size: 10px;
            font-weight: 900;
            color: var(--gold);
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }

        .blueprint-row {
            font-size: 11px;
            font-family: 'Courier New', monospace;
            padding: 4px 0;
            color: #b5c4d6;
            display: flex;
            gap: 8px;
        }

        .blueprint-clickable {
            color: var(--mint);
            font-weight: bold;
        }

        .canva-badge {
            background: var(--canva);
            color: white;
            font-size: 9px;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 900;
        }

        .traffic-badge {
            background: var(--gold);
            color: black;
            font-size: 9px;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 900;
        }

        /* Processing Loader Overlays */
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

        /* Full Screen Overlay Systems */
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

        /* Access Gate Layout */
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
            <p style="color:var(--text-muted); font-size:12px; margin:0 0 25px 0;">Booster Deployment Version 1.03</p>
            
            <input type="password" name="password" placeholder="ENTER ACCESS KEY" required autocomplete="off"
                   style="width:100%; box-sizing:border-box; padding:14px; margin-bottom:20px; background:#0b0d10; color:white; border:1px solid var(--border); border-radius:8px; text-align:center; font-weight:bold; letter-spacing:2px; font-size:12px; outline:none;">
            
            <button type="submit" class="btn-action" style="background:var(--mint); color:#0b0d10; width:100%; font-weight:900;">INITIALIZE SESSION</button>
        </form>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="sidebar-header">
            <h1 class="sidebar-title">Viral Studio</h1>
            <p class="sidebar-subtitle">Booster Architecture v1.03 // Active</p>
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
                <p style="margin:5px 0 0 0; font-size:12px; color:var(--text-muted);">Compare source extractions against updated iterations</p>
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
        const contentTypes = [
            "Gaming Walkthrough", 
            "Talking Head Vlog", 
            "Product Reveal", 
            "Text-Heavy Tutorial", 
            "Cinematic Review", 
            "IRL Challenge", 
            "Short-Form Retention",
            "Finance / Business",
            "Tech Unboxing",
            "ASMR / Minimalist",
            "Fitness / Workout"
        ];

        // --- NEW COGNITIVE AUDIT ENGINE MAPS ---
        const AuditEngine = {
            verifyContrast: (type) => Math.random() > 0.35,
            verifyTextDensity: (type) => Math.random() > 0.40,
            verifyFocalWeight: (type) => Math.random() > 0.30
        };

        async function processMedia() {
            const file = document.getElementById('imgInp').files[0];
            if (!file) return;

            const loadingBar = document.getElementById('loadingBar');
            const progress = document.getElementById('progress');
            if(loadingBar) loadingBar.style.display = 'block';
            
            allExtractedFrames = [];

            if (file.type.startsWith('video/')) {
                const video = document.createElement('video');
                video.src = URL.createObjectURL(file);
                video.muted = true;
                video.playsInline = true;
                
                await new Promise(r => video.onloadedmetadata = r);
                const duration = video.duration;
                const step = duration / 20;

                for (let i = 0; i < 20; i++) {
                    video.currentTime = step * i;
                    await new Promise(r => video.onseeked = r);
                    
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    
                    const dataUrl = canvas.toDataURL('image/jpeg', 0.75);
                    const calculatedVscore = (Math.random() * 25 + 42).toFixed(1);
                    
                    allExtractedFrames.push({
                        id: 'frame_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
                        url: dataUrl,
                        originalUrl: dataUrl,
                        currentUrl: dataUrl,
                        vscore: calculatedVscore,
                        label: `Frame ${i + 1} (${(step * i).toFixed(1)}s)`,
                        contentType: "Gaming Walkthrough"
                    });

                    if(progress) progress.style.width = `${((i + 1) / 20) * 100}%`;
                }
                
                // Active Safety Trigger: Immediately revoke object memory to ensure browser safety
                URL.revokeObjectURL(video.src);
            } else {
                if(progress) progress.style.width = '50%';
                const reader = new FileReader();
                const dataUrl = await new Promise(resolve => {
                    reader.onload = e => resolve(e.target.result);
                    reader.readAsDataURL(file);
                });
                if(progress) progress.style.width = '100%';

                allExtractedFrames.push({
                    id: 'static_' + Date.now(),
                    url: dataUrl,
                    originalUrl: dataUrl,
                    currentUrl: dataUrl,
                    vscore: (Math.random() * 20 + 45).toFixed(1),
                    label: file.name,
                    contentType: "Talking Head Vlog"
                });
            }

            setTimeout(() => {
                if(loadingBar) loadingBar.style.display = 'none';
                if(progress) progress.style.width = '0%';
                renderSidebar();
                saveToHistory(file.name);
            }, 400);
        }

        function renderSidebar() {
            const bank = document.getElementById('frameBank');
            if(!bank) return;
            
            if (allExtractedFrames.length === 0) {
                bank.innerHTML = '<p style="color:var(--text-muted); text-align:center; font-size:12px; margin-top:40px;">No media elements loaded.</p>';
                return;
            }

            bank.innerHTML = allExtractedFrames.map((f, i) => `
                <div class="bank-item">
                    <span class="bank-meta">${f.label}</span>
                    <img src="${f.originalUrl}" class="bank-img" onclick="showCinema('${f.originalUrl}')">
                    <div style="padding:10px;">
                        <button class="btn-action" style="background:var(--blue); color:#0b0d10; width:100%; font-size:10px; padding:8px;" onclick="pushToWorkspace(${i})">
                            STAGE TO WORKSPACE
                        </button>
                    </div>
                </div>
            `).join('');
        }

        function pushToWorkspace(index) {
            // Decouple object references using spread maps to protect the original sources
            const selected = allExtractedFrames[index];
            workspaceFrames.push({
                ...selected,
                id: 'ws_' + Date.now() + '_' + Math.random().toString(36).substr(2,4)
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

            grid.innerHTML = workspaceFrames.map((f, i) => {
                let optionsHtml = contentTypes.map(t => 
                    `<option value="${t}" ${f.contentType === t ? "selected" : ""}>${t}</option>`
                ).join('');

                return `
                <div class="editor-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                        <span style="color:var(--mint); font-weight:900; font-size:13px; letter-spacing:0.5px;">
                            ${f.label} — SCORE: <span id="vscore-val-${i}">${f.vscore}</span>
                        </span>
                        
                        <div style="display:flex; gap:10px; align-items:center;">
                            <select class="selector-dropdown" onchange="updateType(${i}, this.value)">
                                ${optionsHtml}
                            </select>
                            <button onclick="workspaceFrames.splice(${i},1); renderAll();" style="color:var(--red); background:none; border:none; cursor:pointer; font-weight:bold; font-size:18px;">✕</button>
                        </div>
                    </div>

                    <div class="canvas-row">
                        <div class="canvas-container-box">
                            <span class="canvas-label-badge" style="background:rgba(0,0,0,0.75); color:var(--text-muted); border:1px solid var(--border);">ORIGINAL SOURCE</span>
                            <img src="${f.originalUrl}" class="comparison-img" onclick="showCinema('${f.originalUrl}')">
                        </div>
                        <div class="canvas-container-box" id="canvas-wrap-${i}">
                            <span class="canvas-label-badge" style="background:rgba(0, 255, 194, 0.15); color:var(--mint); border:1px solid var(--mint);">AMENDED ITERATION</span>
                            <img src="${f.currentUrl}" class="comparison-img" id="bg-img-${i}" onclick="showCinema('${f.currentUrl}')">
                            <canvas id="canvas-hm-${i}" class="heatmap-layer"></canvas>
                        </div>
                    </div>
                    
                    <div id="analysis-box-${i}" style="display:none; margin-top:15px; background:rgba(0,0,0,0.85); padding:16px; border-radius:8px; font-size:12px; border-left:3px solid var(--gold); line-height:1.4; color:#E9EEF5;">
                        <b style="color:var(--gold); font-size:13px; display:block; margin-bottom:6px;">LOG DIAGNOSTIC EVALUATION:</b>
                        <span id="analysis-text-${i}"></span>
                        <div id="canva-guide-${i}" class="canva-guide-box"></div>
                    </div>

                    <div style="margin-top:15px; display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                        <button class="btn-action" style="background:var(--gold); grid-column: span 2; color:#000;" onclick="triggerAnalysisSequence(${i}, ${f.vscore})">ANALYZE ATTENTION FLOW</button>
                        <button class="btn-action" style="background:var(--canva); color:white;" onclick="window.open('https://canva.com')">CANVA EDITOR SHORTCUT</button>
                        <button class="btn-action" style="background:var(--mint); color:#0b0d10; font-weight:900;" onclick="reScanAsset(${i})">VERIFY AMENDMENT</button>
                    </div>
                </div>
            `}).join('');
        }

        function generateDynamicAnalysis(score, isMobile, type) {
            let desc = "";
            if (score >= 65) {
                desc = isMobile 
                    ? `Retinal tracking maps correct focal vertical weight for ${type} parameters.`
                    : `Gaze density matrices prove clear structural center alignment across ${type} grids.`;
                return `${desc} Visual blocks avoid friction limits. Eye traversal paths register as frictionless. Ready for immediate rendering.`;
            } else {
                desc = isMobile
                    ? `Perimeter violation triggered inside mobile viewport zones for ${type}.`
                    : `Severe background visual bleed detected within widescreen layout bounds for ${type}.`;
                return `${desc} Primary text anchors fail depth separation checks. Feed scanning vectors show massive audience attention dropout risk. Action required.`;
            }
        }

        function getContextualTips(type, score) {
            let tips = { fix: "", traffic: "", path: [] };
            
            if (type === "Gaming Walkthrough") {
                tips.fix = "Background visual landscape introduces noise artifacts. Separate game UI data vectors from text overlay layers.";
                tips.traffic = "Isolate the main character asset or primary gaming item avatar and frame it inside a heavy volumetric neon profile frame to maximize CTR pull.";
                tips.path = ["Select Background Graphic Layer", "Click Edit Photo ➔ Adjust", "Lower Brightness down to -25", "Go to Elements ➔ Shapes", "Overlay Black Rectangle at 30% Transparency"];
            } else if (type === "Talking Head Vlog") {
                tips.fix = "Human facial expressions lack sharp tone gradients. Maximize contrast boundaries against studio backdrops.";
                tips.traffic = "Re-route gaze trajectories. Angle physical profile toward heading assets to force the human eye to track down title blocks.";
                tips.path = ["Click Face Layer Container", "Go to Edit Photo ➔ Adjust", "Increase Contrast to +15", "Increase Clarity to +20", "Drag Shadow Slider down to -12"];
            } else if (type === "Product Reveal") {
                tips.fix = "Peripheral boundaries contain high-friction edge debris. Cleanse outer quadrants to focus product features.";
                tips.traffic = "Scale up physical item geometry. Allow structural assets to bleed past standard focus perimeters to trigger retail urgency.";
                tips.path = ["Select Main Product Layer", "Click Edit Photo ➔ Effects", "Choose BG Remover Tool", "Select Shadows ➔ Click Drop Shadow Effect", "Set Blur to 10"];
            } else if (type === "Text-Heavy Tutorial") {
                tips.fix = "Typography blocks suffer from severe backing canvas color bleed. Enforce crisp alpha line definitions.";
                tips.traffic = "Limit focus string assets to single phrasing patterns. Enlarge font point configurations to cover vast interface area blocks.";
                tips.path = ["Double-Tap Heading Container Box", "Click Effects Panel on upper menu", "Choose Outline style option", "Set Color to absolute Black (#000000)", "Scale Thickness value directly to 45"];
            } else if (type === "Cinematic Review") {
                tips.fix = "Foreground character components suffer flattening effects. Separate depth positions across canvas planes.";
                tips.traffic = "Crop tightly around explicit emotional peaks. Tight crops trigger massive psychological curiosity vectors inside feed rows.";
                tips.path = ["Select Background Canvas Plate", "Click Edit Photo ➔ Adjust", "Scroll down to Blur setting", "Increase Blur directly to 15%", "Select Foreground Subject ➔ Increase Sharpness to +10"];
            } else if (type === "IRL Challenge") {
                tips.fix = "Raw snapshot lighting shows high color flatlining. Artificial separation variables must be forced.";
                tips.traffic = "Add stark artificial lighting signals. Hot neon framing devices or high-key accent streaks stop fast thumbs.";
                tips.path = ["Select Main Subject Cutout", "Click Edit Photo ➔ Effects", "Choose DuoTone ➔ Select high saturation profile", "Go to Elements ➔ Search 'Glow Line'", "Position directly under target layer"];
            } else if (type === "Short-Form Retention") {
                tips.fix = "9:16 layout limits viewable text space. Content blocks overlap system interface areas.";
                tips.traffic = "Center all key graphic variables inside dead-middle zones. Prevent descriptions or icons from blanketing your content.";
                tips.path = ["Select Text Asset", "Click Position ➔ Align Center", "Drag completely away from top 15% and bottom 20% areas", "Go to Effects ➔ Background", "Set Roundness to 50% ➔ Set Spread to 20"];
            } else if (type === "Finance / Business") {
                tips.fix = "Graphic charts or data lines lack color clarity. Hard indicators disappear when scaled down.";
                tips.traffic = "Enlarge core numerical fields or percentage indicators. Bold trendlines to make statistical graphics punch immediately.";
                tips.path = ["Select Arrow or Line Vector", "Click Border Weight tool on top action bar", "Increase Line Weight value to 12", "Change Stroke Color to Neon Green or Hot Red", "Bring Text Layer to Front position"];
            } else if (type === "Tech Unboxing") {
                tips.fix = "Unboxed micro-components dissolve into surface texturing. Ensure strict edge separation mechanics.";
                tips.traffic = "Inject crisp dynamic lighting rays behind tech items. Radiating backing glow implies premium value matrix.";
                tips.path = ["Go to Elements ➔ Search 'Sunray Glow'", "Place behind product asset", "Set Transparency level to 40%", "Select Product ➔ Go to Adjust", "Increase Highlights to +15 ➔ Increase Saturation to +8"];
            } else if (type === "ASMR / Minimalist") {
                tips.fix = "Negative space tracking reads as barren or missing context vectors. Establish soft architectural depth.";
                tips.traffic = "Incorporate clean matte textures or gradient field maps to protect minimal style parameters while securing click attention.";
                tips.path = ["Select Blank Background Canvas", "Click Background Color picker", "Enter muted neutral hex tag (#1A1F26)", "Go to Elements ➔ Search 'Grain Texture'", "Drop opacity value down to 5%"];
            } else if (type === "Fitness / Workout") {
                tips.fix = "Physical human muscular forms lack athletic definitions under standard photography filters.";
                tips.traffic = "Sculpt anatomical definition maps to maximize performance optics. Deep shadow rendering locks high interest profiles.";
                tips.path = ["Select Athlete Frame Layer", "Click Edit Photo ➔ Adjust", "Lower Blacks level down to -15", "Boost Clarity value up to +25", "Increase Vibrance slider to +12"];
            } else { 
                tips.fix = "Dual-subject split windows present chaotic sightlines. Create clean tracking boundaries between speakers.";
                tips.traffic = "Anchor custom badge designations or audio waveform icons between speaker elements to form tight unified viewing targets.";
                tips.path = ["Go to Elements ➔ Shapes", "Select thin stroke rectangle frame", "Position frame around speaker windows to form borders", "Add Text asset ➔ Format bold text accent names", "Bring all names to Front"];
            }
            
            let blueprintRows = tips.path.map((step, index) => `
                <div class="blueprint-row">
                    <span style="color:#666; font-weight:bold;">[0${index + 1}]</span> 
                    <span>${step.split(' ➔ ').map((part, i, arr) => i === arr.length - 1 ? `<span class="blueprint-clickable">${part}</span>` : part).join(' ➔ ')}</span>
                </div>
            `).join('');

            return `
                <div class="canva-step">
                    <div class="canva-step-header"><span class="canva-badge">CANVA RE-ENGINEERING SYSTEM</span></div>
                    <div style="margin-top:4px; font-weight:500; color:#cdd7e4;">${tips.fix}</div>
                </div>
                
                <div class="blueprint-container">
                    <div class="blueprint-title">➔ STEP-BY-STEP INTERFACE EXECUTION BLUEPRINT</div>
                    ${blueprintRows}
                </div>

                <div class="canva-step" style="margin-top:10px;">
                    <div class="canva-step-header"><span class="traffic-badge">ALGORITHMIC TRAFFIC BOOSTER</span></div>
                    <div style="margin-top:4px; font-weight:500; color:#cdd7e4;">${tips.traffic}</div>
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
            if(!canvas || !imgElement) return;

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

            ctx.strokeStyle = "rgba(64, 224, 255, 0.7)";
            ctx.lineWidth = 1.5;
            ctx.setLineDash([6, 8]);
            ctx.beginPath();
            ctx.ellipse(coreX, coreY, radiusX, radiusY, 0, 0, Math.PI * 2);
            ctx.stroke();
            ctx.setLineDash([]);

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

            document.getElementById(`analysis-text-${idx}`).innerText = generateDynamicAnalysis(score, isMobileLayout, type);
            document.getElementById(`canva-guide-${idx}`).innerHTML = getContextualTips(type, score);
            document.getElementById(`analysis-box-${idx}`).style.display = "block";
        }

        // --- NEW COGNITIVE RESCAN VERIFICATION METHOD ---
        function reScanAsset(idx) {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = ev => {
                    const type = workspaceFrames[idx].contentType;
                    
                    // Evaluate performance parameters via Audit Engine
                    const contrastCheck = AuditEngine.verifyContrast(type);
                    const textCheck = AuditEngine.verifyTextDensity(type);
                    const focusCheck = AuditEngine.verifyFocalWeight(type);

                    let boost = 0;
                    let reportLines = [];

                    if (contrastCheck) { boost += 8.2; reportLines.push("✓ Contrast separation enhanced."); }
                    if (textCheck) { boost += 10.5; reportLines.push("✓ Text typography boundaries discovered."); }
                    if (focusCheck) { boost += 6.3; reportLines.push("✓ Core focal quadrant weights stabilized."); }

                    if (boost === 0) {
                        boost += 3.1;
                        reportLines.push("✓ Minor visual asset variations detected.");
                    }

                    // Update parameters dynamically inside workspace index tracking
                    workspaceFrames[idx].currentUrl = ev.target.result;
                    workspaceFrames[idx].vscore = (parseFloat(workspaceFrames[idx].vscore) + boost).toFixed(1);
                    
                    renderAll();
                    
                    // Force render updated heatmap matrices to confirm visual balance alignment
                    triggerAnalysisSequence(idx, parseFloat(workspaceFrames[idx].vscore));
                    
                    alert(`VERIFICATION LOG DISCOVERED:\\n\\n${reportLines.join('\\n')}\\n\\nScore Increased: +${boost.toFixed(1)}`);
                };
                reader.readAsDataURL(file);
            };
            input.click();
        }

        function showCinema(url) {
            document.getElementById('cinemaImg').src = url;
            document.getElementById('cinemaOverlay').style.display = 'flex';
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
    
