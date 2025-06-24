# manual_test.py

from src.ingestion.processors import process_file
import os

def test_file(filepath, save_to_disk=False):
    text = process_file(filepath)
    print(f"✅ Estratto da: {filepath}")
    print(f"🔍 Lunghezza testo: {len(text)} caratteri\n")
    # Stampa i primi 500 caratteri per comodità
    print(text[:500] + ("…" if len(text) > 500 else ""))
    print("-" * 60 + "\n")
    if save_to_disk:
        out_dir = "data/processed"
        os.makedirs(out_dir, exist_ok=True)
        name = os.path.splitext(os.path.basename(filepath))[0] + ".txt"
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"💾 Salvato full-text in: {out_dir}/{name}\n")

if __name__ == "__main__":
    raw_dir = "data/raw"
    # Prova sample.txt e il PDF
    #  test_file(os.path.join(raw_dir, "sample.txt"))
    test_file(os.path.join(raw_dir, "Lecture 02 - Error Control Protocols .pdf"))

    # Testa automaticamente tutte le immagini in data/raw
    # for fname in os.listdir(raw_dir):
    #    if fname.lower().endswith((".jpg", ".jpeg", ".png")):
    #        test_file(os.path.join(raw_dir, fname), save_to_disk=True)

