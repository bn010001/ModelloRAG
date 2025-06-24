import os
import fitz  # PyMuPDF
import pytesseract
import subprocess
import logging
from PIL import Image
import pandas as pd

# (opzionale) per image captioning multimodale
from transformers import BlipProcessor, BlipForConditionalGeneration
from src.ingestion.pdf_images import extract_pdf_images_with_caption

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Inizializza il modello BLIP una sola volta (captioning)
try:
    _blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    _blip_model     = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
except Exception:
    _blip_processor = _blip_model = None
    logger.warning("BLIP non disponibile, disabilitato captioning immagini.")

class BaseProcessor:
    def __init__(self, filepath):
        self.filepath = filepath

    def extract(self):
        raise NotImplementedError

class TxtProcessor(BaseProcessor):
    def extract(self):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return f.read()

class ExcelProcessor(BaseProcessor):
    def extract(self):
        df = pd.read_excel(self.filepath)
        return df.to_csv(index=False)

class PDFProcessor(BaseProcessor):
    def extract(self):
        doc = fitz.open(self.filepath)
        return "\n".join(page.get_text() for page in doc)

class PDFOCRProcessor(BaseProcessor):
    def extract(self):
        output_pdf = self.filepath.replace(".pdf", "_ocr.pdf")
        # forziamo OCR anche su PDF tagged
        cmd = [
            "ocrmypdf",
            "--force-ocr",
            self.filepath,
            output_pdf
        ]
        subprocess.run(cmd, check=True)
        doc = fitz.open(output_pdf)
        return "\n".join(page.get_text() for page in doc)

class ImageProcessor(BaseProcessor):
    def extract(self):
        # OCR puro
        img = Image.open(self.filepath).convert("L")
        ocr_text = pytesseract.image_to_string(img, lang="ita+eng", config="--psm 6")
        # captioning (se BLIP disponibile)
        caption = ""
        if _blip_processor and _blip_model:
            inputs = _blip_processor(images=img, return_tensors="pt")
            out    = _blip_model.generate(**inputs, max_new_tokens=50)
            caption = _blip_processor.decode(out[0], skip_special_tokens=True)
            caption = f"\n[Caption] {caption}"
        return (ocr_text.strip() + caption).strip()

def is_pdf_native(filepath, pages_to_check=3, char_threshold=300):
    """Ritorna True se il PDF contiene sufficiente testo nativo."""
    doc = fitz.open(filepath)
    total = 0
    for page in doc[:min(pages_to_check, len(doc))]:
        total += len(page.get_text().strip())
    avg = total / pages_to_check if pages_to_check else 0
    return avg > char_threshold

def process_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".txt":
        return TxtProcessor(filepath).extract()

    if ext == ".xlsx":
        return ExcelProcessor(filepath).extract()

    if ext == ".pdf":
        if is_pdf_native(filepath):
            text = PDFProcessor(filepath).extract()
        else:
            text = PDFOCRProcessor(filepath).extract()
    
        # Estrai le immagini e le caption
        img_map = extract_pdf_images_with_caption(filepath)

        # Opzionale: includi le descrizioni nel testo estratto
        for item in img_map:
            desc = f"\n[Figura da Pag.{item['page'] + 1}] {item['caption']}"
            if item['caption']:
                text += desc

        return text

    if ext in [".jpg", ".jpeg", ".png"]:
        return ImageProcessor(filepath).extract()

    raise ValueError(f"Formato non supportato: {ext}")
