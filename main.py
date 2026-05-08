import os, boto3, fal_client, time
from flask import Flask, request, jsonify, render_template_string, redirect

app = Flask(__name__)

# --- CONFIG ---
LAB_PASSWORD = os.environ.get("LAB_PASSWORD", "HEATHUMB2026")
s3 = boto3.client('s3', region_name='eu-west-2')
BUCKET = os.environ.get("AWS_BUCKET_NAME")

# --- HTML STYLES (Carbon Mint) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <style>
        body { background: #0B0D10; color: #E9EEF5; font-family: 'Inter', sans-serif; text-align: center; padding: 40px; }
        .card { background: #151A21; border: 1px solid #273140; border-radius: 24px; padding: 30px; max-width: 500px; margin: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        h1 { color: #00FFC2; font-weight: 800; letter-spacing: -1px; }
        input { width: 80%; padding: 12px; border-radius: 12px; border: 1px solid #273140; background: #0B0D10; color: white; margin-bottom: 20px; }
        .btn { background: linear-gradient(135deg, #00FFC2, #40E0FF); color: #0B0D10; font-weight: bold; padding: 14px 28px; border: none; border-radius: 12px; cursor: pointer; transition: 0.3s; }
        .btn:hover { transform: scale(1.05); box-shadow: 0 0 20px rgba(0, 255, 194, 0.4); }
    </style>
</head>
<body>
    <div class="card">
        <h1>HEATHUMB LAB <span style="font-size: 12px; vertical-align: middle; color: #40E0FF; border: 1px solid #40E0FF; padding: 2px 6px; border-radius: 4px;">BETA</span></h1>
        {% if not authorized %}
            <p>Enter Access Code to Unlock Neural Engine</p>
            <form method="GET" action="/lab">
                <input type="password" name="code" placeholder="Enter Password...">
                <button type="submit" class="btn">ENTER LAB</button>
            </form>
        {% else %}
            <p>Authenticated. Ready for Neural Extraction.</p>
            <form action="/process" method="POST" enctype="multipart/form-data">
                <input type="file" name="video" accept="video/*" style="border:none;">
                <button type="submit" class="btn">START ANALYSIS</button>
            </form>
        {% endif %}
    </div>
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
    video = request.files['video']
    filename = f"lab_{int(time.time())}.mp4"
    
    # 1. Upload to S3
    s3.upload_fileobj(video, BUCKET, filename)
    video_url = f"https://{BUCKET}.s3.amazonaws.com/{filename}"
    
    # 2. Extract 20 Frames (The Library)
    extract = fal_client.subscribe("fal-ai/ffmpeg-api/extract-frame", {"video_url": video_url, "count": 20})
    frames = [img['url'] for img in extract['images']]
    
    # 3. Create 4 AI Remixes (The +4)
    remixes = []
    for i in range(4):
        res = fal_client.subscribe("fal-ai/flux-pro", {
            "image_url": frames[0],
            "prompt": "YouTube thumbnail, high contrast, glowing neon borders, sharp icons, 4k",
            "strength": 0.4
        })
        remixes.append(res['images'][0]['url'])
    
    # 4. Cleanup: Delete video immediately
    s3.delete_object(Bucket=BUCKET, Key=filename)
    
    return jsonify({
        "status": "success",
        "real_extracts": frames[:6],
        "ai_remixes": remixes,
        "library": frames
    })

if __name__ == "__main__":
    app.run(port=8080)
