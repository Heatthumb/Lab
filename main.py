import os
import boto3
import fal_client
import time
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- AUTH & CONFIG ---
# This ensures the fal_client library sees your API key from Railway
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")

# Password for your testers
LAB_PASSWORD = os.environ.get("LAB_PASSWORD", "HEATHUMB2026")

# AWS Setup (Stockholm Region)
s3 = boto3.client('s3', region_name='eu-north-1')
BUCKET = os.environ.get("AWS_BUCKET_NAME", "heatthumb-vault-sruli")

# --- DESIGN (Carbon Mint) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HEATHUMB LAB</title>
    <style>
        body { background: #0B0D10; color: #E9EEF5; font-family: 'Inter', sans-serif; text-align: center; padding: 40px; }
        .card { background: #151A21; border: 1px solid #273140; border-radius: 24px; padding: 40px; max-width: 600px; margin: auto; box-shadow: 0 10px 40px rgba(0,0,0,0.6); }
        h1 { color: #00FFC2; font-weight: 800; letter-spacing: -2px; font-size: 32px; margin-bottom: 10px; }
        p { color: #8A94A6; margin-bottom: 30px; }
        input[type="password"], input[type="file"] { width: 90%; padding: 14px; border-radius: 12px; border: 1px solid #273140; background: #0B0D10; color: white; margin-bottom: 20px; outline: none; }
        .btn { background: linear-gradient(135deg, #00FFC2, #40E0FF); color: #0B0D10; font-weight: bold; padding: 16px 32px; border: none; border-radius: 12px; cursor: pointer; transition: 0.3s; font-size: 16px; width: 100%; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 0 25px rgba(0, 255, 194, 0.4); }
        .footer { margin-top: 40px; font-size: 12px; color: #4A5568; }
    </style>
</head>
<body>
    <div class="card">
        <h1>HEATHUMB LAB <span style="font-size: 12px; vertical-align: middle; color: #40E0FF; border: 1px solid #40E0FF; padding: 3px 8px; border-radius: 6px; letter-spacing: 1px;">NEURAL V1</span></h1>
        
        {% if not authorized %}
            <p>Enter your tester access code to unlock the engine.</p>
            <form method="GET" action="/lab">
                <input type="password" name="code" placeholder="Access Code..." required>
                <button type="submit" class="btn">UNLOCK ENGINE</button>
            </form>
        {% else %}
            <p>Authenticated. Upload video for frame extraction and AI remixing.</p>
            <form action="/process" method="POST" enctype="multipart/form-data">
                <input type="file" name="video" accept="video/*" required>
                <button type="submit" class="btn">START NEURAL ANALYSIS</button>
            </form>
        {% endif %}
    </div>
    <div class="footer">Powered by Heatthumb Neural Engine & fal.ai</div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, authorized=False)

@app.route('/lab')
def lab():
    code = request.args.get('code')
    if code == LAB_PASSWORD:
        return render_template_string(HTML_TEMPLATE, authorized=True)
    return "Invalid Code. Access Denied.", 403

@app.route('/process', methods=['POST'])
def process():
    if 'video' not in request.files:
        return "No video uploaded", 400
    
    video = request.files['video']
    filename = f"lab_{int(time.time())}.mp4"
    
    try:
        # 1. Upload to S3
        s3.upload_fileobj(video, BUCKET, filename)
        # Regional URL for Stockholm
        video_url = f"https://{BUCKET}.s3.eu-north-1.amazonaws.com/{filename}"
        
        # 2. Extract 20 Frames (The Library)
        # Using the fal.ai ffmpeg-api
        extract = fal_client.subscribe("fal-ai/ffmpeg-api/extract-frame", {
            "video_url": video_url, 
            "count": 20
        })
        all_frames = [img['url'] for img in extract['images']]
        
        # 3. Create 4 AI Remixes (The +4)
        # We take the first extracted frame and enhance it
        remixes = []
        for i in range(4):
            # Using Flux Pro for high-end thumbnail remixing
            res = fal_client.subscribe("fal-ai/flux-pro", {
                "image_url": all_frames[0],
                "prompt": "Professional YouTube thumbnail, high contrast, glowing neon borders, sharp gaming icons, 4k resolution, cinematic lighting",
                "strength": 0.45
            })
            remixes.append(res['images'][0]['url'])
        
        # 4. Cleanup: Delete video immediately to keep AWS costs at £0
        s3.delete_object(Bucket=BUCKET, Key=filename)
        
        return jsonify({
            "status": "success",
            "real_extracts_6": all_frames[:6],
            "ai_remixes_4": remixes,
            "full_library_20": all_frames
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Railway uses port 8080 by default
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
