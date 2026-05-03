from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime
import subprocess
import sys

from model_logic import load_models, analyze_image
from firebase_connection import save_result

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

SHOW_PREVIEW = True

print("[DEBUG] Loading models for server...")
yolo_coco, yolo_helmet = load_models()
print("[DEBUG] Server models loaded successfully.")


@app.route("/")
def home():
    """Simple route to check that the server is running."""
    return "Server is running!"


@app.route("/analyze", methods=["POST"])
def analyze():
    """Receive image from Raspberry Pi, analyze it, save the result, and return JSON."""
    try:
        # make sure image file was sent
        if "image" not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        file = request.files["image"]

        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        # save image with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        save_path = UPLOADS_DIR / filename

        file.save(save_path)
        print(f"[DEBUG] Image saved to: {save_path}")

        # analyze image with the models
        result_dict, pretty_text, original, annotated = analyze_image(
            str(save_path), yolo_coco, yolo_helmet
        )

        # open preview window in a separate process
        if SHOW_PREVIEW:
            try:
                subprocess.Popen(
                    [sys.executable, "preview_display.py", str(save_path)],
                    cwd=str(BASE_DIR)
                )
                print("[DEBUG] Preview process started.")
            except Exception as e:
                print(f"[ERROR] Failed to start preview process: {e}")

        # save result in firestore
        save_result(result_dict)

        print("[DEBUG] Analysis complete.")
        print(result_dict)

        # send result back to raspberry pi
        return jsonify({
            "message": "Image received and analyzed successfully",
            "result": result_dict,
            "pretty_text": pretty_text
        })

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500