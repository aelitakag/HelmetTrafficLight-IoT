from pathlib import Path

import numpy as np
from PIL import Image
from ultralytics import YOLO
from huggingface_hub import hf_hub_download
from supervision import Detections, BoxAnnotator, LabelAnnotator

# main settings
CONF_COCO = 0.25
CONF_HELMET = 0.25
REQUIRED_RATIO = 1.0

BASE_DIR = Path(__file__).resolve().parent


def iou(a, b):
    """Calculate intersection over union between two boxes."""
    xa1, ya1, xa2, ya2 = a
    xb1, yb1, xb2, yb2 = b

    inter = max(0, min(xa2, xb2) - max(xa1, xb1)) * max(0, min(ya2, yb2) - max(ya1, yb1))
    if inter <= 0:
        return 0.0

    area_a = max(0, xa2 - xa1) * max(0, ya2 - ya1)
    area_b = max(0, xb2 - xb1) * max(0, yb2 - yb1)
    union = area_a + area_b - inter + 1e-6

    return inter / union


def center(box):
    """Return the center point of a box."""
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def overlap_1d(a1, a2, b1, b2):
    """Calculate overlap between two 1D ranges."""
    return max(0, min(a2, b2) - max(a1, b1))


def top_head_box(person_xyxy, frac=0.35):
    """Take the top part of a person box as the head area."""
    x1, y1, x2, y2 = person_xyxy
    h = y2 - y1
    return [x1, y1, x2, y1 + frac * h]


def nms(boxes, scores, iou_thr=0.5):
    """Apply simple non maximum suppression on person boxes."""
    if not boxes:
        return []

    idxs = sorted(range(len(boxes)), key=lambda i: scores[i], reverse=True)
    keep = []

    while idxs:
        i = idxs.pop(0)
        keep.append(i)
        idxs = [j for j in idxs if iou(boxes[i], boxes[j]) < iou_thr]

    return keep


def is_rider(person_box, bike_boxes):
    """Check if a detected person should be counted as a rider."""
    px1, py1, px2, py2 = person_box
    pw, ph = px2 - px1, py2 - py1

    for m in bike_boxes:
        mx1, my1, mx2, my2 = m
        mw, mh = mx2 - mx1, my2 - my1

        # check overlap between person and motorcycle
        xa1, ya1, xa2, ya2 = person_box
        xb1, yb1, xb2, yb2 = m
        inter = max(0, min(xa2, xb2) - max(xa1, xb1)) * max(0, min(ya2, yb2) - max(ya1, yb1))
        if inter > 0.03 * ((xa2 - xa1) * (ya2 - ya1) + (xb2 - xb1) * (yb2 - yb1) - inter + 1e-6):
            return True

        # check if the person center is inside an expanded motorcycle area
        cx, cy = center(person_box)
        expand = 0.15
        ex1 = mx1 - expand * mw
        ex2 = mx2 + expand * mw
        ey1 = my1 - expand * mh
        ey2 = my2 + expand * mh
        if ex1 <= cx <= ex2 and ey1 <= cy <= ey2:
            return True

        # check horizontal overlap and vertical distance
        horiz = overlap_1d(px1, px2, mx1, mx2)
        if horiz >= 0.35 * max(pw, mw) and abs(cy - (my1 + my2) / 2) < 0.25 * max(mh, ph):
            return True

    return False


def load_models():
    """Load the COCO model and the helmet detection model."""
    print("Loading models... (first time may download weights)")

    coco = YOLO("yolov8n.pt")

    helmet_pt = hf_hub_download(
        repo_id="sharathhhhh/safetyHelmet-detection-yolov8",
        filename="best.pt"
    )
    helmet = YOLO(helmet_pt)

    print("Models loaded successfully!")
    return coco, helmet


def overlay_detections(det, base_img):
    """Draw detections and labels on the image."""
    if det and len(det.boxes) > 0:
        d = Detections(
            xyxy=det.boxes.xyxy.cpu().numpy(),
            class_id=det.boxes.cls.cpu().numpy().astype(int),
            confidence=det.boxes.conf.cpu().numpy()
        )
        labels = [det.names[c] for c in d.class_id]

        box_annotator = BoxAnnotator(thickness=3)
        label_annotator = LabelAnnotator(text_scale=1.2, text_thickness=2)

        out = box_annotator.annotate(base_img, d)
        return label_annotator.annotate(out, d, labels=labels)

    return base_img


def analyze_image(path, yolo_coco, yolo_helmet):
    """Run the full image analysis and return the result."""
    original = Image.open(path).convert("RGB")

    # detect persons and motorcycles with COCO
    r_coco = yolo_coco.predict(path, conf=CONF_COCO, verbose=False)[0]
    names_coco = r_coco.names

    person_boxes_raw = []
    person_scores = []
    bike_boxes = []

    for b in r_coco.boxes:
        cls_name = names_coco[int(b.cls)]
        box = b.xyxy[0].tolist()
        score = float(b.conf.item()) if hasattr(b.conf, "item") else float(b.conf)

        if cls_name == "person":
            person_boxes_raw.append(box)
            person_scores.append(score)
        elif cls_name == "motorcycle":
            bike_boxes.append(box)

    keep_idx = nms(person_boxes_raw, person_scores, iou_thr=0.5)
    person_boxes = [person_boxes_raw[i] for i in keep_idx]

    has_moto = len(bike_boxes) > 0
    persons_total = len(person_boxes)

    # detect helmets
    r_helmet = yolo_helmet.predict(path, conf=CONF_HELMET, verbose=False)[0]
    names_h = r_helmet.names

    with_helmet_boxes = []
    without_helmet_boxes = []

    for b in r_helmet.boxes:
        label = names_h[int(b.cls)].strip().lower().replace("_", " ")
        box = b.xyxy[0].tolist()

        if label == "helmet" or label.startswith("with helmet"):
            with_helmet_boxes.append(box)
        elif label.startswith("without helmet") or label == "no helmet":
            without_helmet_boxes.append(box)

    # decide which persons are riders
    rider_mask = [False] * persons_total
    for i, p in enumerate(person_boxes):
        rider_mask[i] = is_rider(p, bike_boxes)

    riders_total = sum(rider_mask)

    # check helmet state for each rider
    riders_with_helmet = 0
    riders_without_helmet = 0
    riders_ambiguous = 0

    for i, p in enumerate(person_boxes):
        head = top_head_box(p, frac=0.35)
        pos = any(iou(head, h) > 0.05 for h in with_helmet_boxes)
        neg = any(iou(head, nh) > 0.05 for nh in without_helmet_boxes)

        if pos and not neg:
            if rider_mask[i]:
                riders_with_helmet += 1
        elif neg and not pos:
            if rider_mask[i]:
                riders_without_helmet += 1
        elif pos and neg:
            if rider_mask[i]:
                riders_ambiguous += 1
        else:
            if rider_mask[i]:
                riders_without_helmet += 1

    # decide if green light is allowed
    allow_green = True
    if riders_total > 0:
        ratio = riders_with_helmet / riders_total
        allow_green = ratio >= REQUIRED_RATIO

    # text for preview window
    pretty_text = (
        f"Motorcycle: {'Detected' if has_moto else 'Not detected'}\n"
        f"People in scene: {persons_total} | Riders: {riders_total}\n"
        f"Helmets on riders: {riders_with_helmet}/{riders_total}"
        + (f" | Ambiguous: {riders_ambiguous}" if riders_ambiguous else "")
    )

    # create annotated image
    annotated_np = np.array(original.copy())
    annotated_np = overlay_detections(r_coco, annotated_np)
    annotated_np = overlay_detections(r_helmet, annotated_np)
    annotated_img = Image.fromarray(annotated_np)

    # keep JSON counts consistent
    riders_without_helmet = max(0, riders_total - riders_with_helmet - riders_ambiguous)

    # main result dictionary
    result_dict = {
        "image_path": str(path),
        "has_motorcycle": int(has_moto),
        "persons_total": int(persons_total),
        "riders_total": int(riders_total),
        "riders_with_helmet": int(riders_with_helmet),
        "riders_without_helmet": int(riders_without_helmet),
        "riders_ambiguous": int(riders_ambiguous),
        "required_ratio": float(REQUIRED_RATIO),
        "allow_green": bool(allow_green),
    }

    return result_dict, pretty_text, original, annotated_img