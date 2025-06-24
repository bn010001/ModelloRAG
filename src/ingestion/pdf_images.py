from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import pytesseract, fitz, cv2, os, json, numpy as np

# Inizializza BLIP-base
_blip_p = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
_blip_m = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def is_diagram(path, line_thresh=10):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    edges = cv2.Canny(img, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=40, maxLineGap=5)
    return lines is not None and len(lines) > line_thresh

def extract_pdf_images_with_caption(pdf_path, out_dir="data/processed/images", output_json="data/processed/image_map.json"):
    os.makedirs(out_dir, exist_ok=True)
    image_map = []
    doc = fitz.open(pdf_path)

    for i, page in enumerate(doc):
        for j, imginfo in enumerate(page.get_images(full=True)):
            xref = imginfo[0]
            pix = fitz.Pixmap(doc, xref)
            ext = "png" if pix.alpha else "jpg"
            fname = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_p{i}_i{j}.{ext}"
            out_path = os.path.join(out_dir, fname)
            pix.save(out_path); pix = None

            # OCR interno
            ocr_labels = pytesseract.image_to_string(
                Image.open(out_path).convert("L"), lang="ita+eng", config="--psm 6"
            ).splitlines()
            ocr_labels = [l for l in ocr_labels if l.strip()]

            # Caption BLIP-base
            img = Image.open(out_path).convert("RGB")
            inputs = _blip_p(images=img, return_tensors="pt")
            out_ids = _blip_m.generate(**inputs, max_new_tokens=50)
            caption = _blip_p.decode(out_ids[0], skip_special_tokens=True).strip()

            # Componi descrizione
            desc = ""
            if ocr_labels:
                desc += "Labels: " + "; ".join(ocr_labels) + ". "
            desc += "Caption: " + caption

            image_map.append({
                "source_pdf": os.path.basename(pdf_path),
                "page": i,
                "image_path": out_path,
                "is_diagram": bool(is_diagram(out_path)),
                "caption": desc
            })

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(image_map, f, indent=2, ensure_ascii=False)
    return image_map
