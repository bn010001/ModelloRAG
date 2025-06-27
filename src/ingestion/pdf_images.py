# src/ingestion/pdf_images.py
from PIL import Image
import os, json, fitz, pytesseract, cv2, numpy as np, io
from transformers import BlipProcessor, BlipForConditionalGeneration

# Inizializza BLIP una volta
_blip_p = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base",  use_fast=True)
_blip_m = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def is_diagram(path, line_thresh=10):
    import cv2, numpy as np
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    edges = cv2.Canny(img, 50, 150)
    lines = cv2.HoughLinesP(edges,1, np.pi/180, threshold=50, minLineLength=40, maxLineGap=5)
    return lines is not None and len(lines) > line_thresh

def extract_pdf_images_with_caption(pdf_path, out_dir="data/processed/images"):
    """
    Estrae tutte le immagini dal PDF, salva su disco e ritorna 
    una lista di dict con caption & metadata. NON scrive il JSON.
    """
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

            # OCR labels
            try:
                ocr_lines = pytesseract.image_to_string(
                    Image.open(out_path).convert("L"),
                    lang="ita+eng", config="--psm 6"
                ).splitlines()
                ocr_labels = [l for l in ocr_lines if l.strip()]
            except:
                ocr_labels = []

            # BLIP caption
            caption = ""
            if _blip_p and _blip_m:
                try:
                    img = Image.open(out_path).convert("RGB")
                    inputs = _blip_p(images=img, return_tensors="pt", input_data_format="HWC")
                    out_ids = _blip_m.generate(**inputs, max_new_tokens=50)
                    caption = _blip_p.decode(out_ids[0], skip_special_tokens=True).strip()
                except:
                    caption = "(errore caption)"

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

    return image_map
