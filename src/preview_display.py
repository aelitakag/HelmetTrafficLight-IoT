import tkinter as tk
from PIL import ImageTk, Image


def show_preview(original_image, annotated_image, pretty_text):
    root = tk.Tk()
    root.title("Helmet Detection Preview")
    root.geometry("1600x850")
    root.configure(bg="#f7f7f8")

    def fit_to_box(pil_img, box_w, box_h, bg="#f7f7f8"):
        w, h = pil_img.size
        scale = min(box_w / w, box_h / h)

        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        resized = pil_img.resize((new_w, new_h))
        canvas = Image.new("RGB", (box_w, box_h), bg)

        off = ((box_w - new_w) // 2, (box_h - new_h) // 2)
        canvas.paste(resized, off)

        return canvas

    # title
    top = tk.Frame(root, bg="#f7f7f8")
    top.pack(fill="x", pady=10)

    tk.Label(
        top,
        text="Helmet Detection Result",
        bg="#f7f7f8",
        font=("Arial", 22, "bold")
    ).pack()

    # images section
    mid = tk.Frame(root, bg="#f7f7f8")
    mid.pack(fill="x", pady=5)

    left = tk.Frame(mid, bg="#f7f7f8")
    left.pack(side="left", expand=True)

    right = tk.Frame(mid, bg="#f7f7f8")
    right.pack(side="left", expand=True)

    tk.Label(
        left,
        text="Original Image",
        bg="#f7f7f8",
        font=("Arial", 14, "bold")
    ).pack(pady=4)

    tk.Label(
        right,
        text="Annotated Image",
        bg="#f7f7f8",
        font=("Arial", 14, "bold")
    ).pack(pady=4)

    # balanced image size
    original_fitted = fit_to_box(original_image, 650, 500)
    annotated_fitted = fit_to_box(annotated_image, 650, 500)

    tk_original = ImageTk.PhotoImage(original_fitted)
    tk_annotated = ImageTk.PhotoImage(annotated_fitted)

    panel_orig = tk.Label(left, image=tk_original, bg="#f7f7f8")
    panel_orig.image = tk_original
    panel_orig.pack()

    panel_anno = tk.Label(right, image=tk_annotated, bg="#f7f7f8")
    panel_anno.image = tk_annotated
    panel_anno.pack()

    # result text
    bottom = tk.Frame(root, bg="#f7f7f8")
    bottom.pack(fill="x", pady=10)

    tk.Label(
        bottom,
        text=pretty_text,
        bg="#f7f7f8",
        font=("Arial", 15),
        justify="left"
    ).pack()

    root.mainloop()


def run_preview_from_path(image_path):
    """Analyze a given image path and display the preview."""
    from model_logic import load_models, analyze_image

    yolo_coco, yolo_helmet = load_models()

    result, pretty, original, annotated = analyze_image(
        str(image_path), yolo_coco, yolo_helmet
    )

    show_preview(original, annotated, pretty)


if __name__ == "__main__":
    import sys

    try:
        if len(sys.argv) > 1:
            run_preview_from_path(sys.argv[1])
        else:
            print("[ERROR] No image path provided")

    except Exception as e:
        print(f"[ERROR] {e}")