import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
from datetime import datetime

# path to firebase credentials file
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "helmet-iot-8789a-firebase-adminsdk-fbsvc-cdef92eb72.json"

# initialize firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate(CREDENTIALS_FILE)
    firebase_admin.initialize_app(cred)

# create firestore client
db = firestore.client()


def save_result(result_dict):
    try:
        # create document id based on current time
        doc_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        # copy data so we don't change original
        data = dict(result_dict)

        # add timestamp fields
        data["saved_at"] = firestore.SERVER_TIMESTAMP
        data["saved_at_text"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # save to firestore
        db.collection("detections").document(doc_id).set(data)

        print("[INFO] result saved successfully")

    except Exception as e:
        print(f"[ERROR] saving failed: {e}")