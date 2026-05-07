import os
import stripe
from flask import Flask, redirect, request, jsonify

app = Flask(__name__)

# 1. Setup your Secret Keys from Railway Variables
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PAYMENT_LINK = "PASTE_YOUR_STRIPE_LINK_HERE" # You can update this later

@app.route('/')
def home():
    return "HeatThumb Lab is Online. Ready for processing."

# 2. The 'Buy' Route - send them to Stripe
@app.route('/buy')
def buy():
    # In a real launch, this would be your Stripe Payment Link
    return redirect(STRIPE_PAYMENT_LINK)

# 3. The "Process" Route (Where the AI work happens)
@app.route('/process', methods=['POST'])
def process_video():
    # This is where we will add the AWS and FAL.ai logic next
    return jsonify({"status": "Success", "message": "Video received for processing"})

if __name__ == "__main__":
    # Railway needs the app to run on port 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)