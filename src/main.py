# src/main.py (o un file di test separato)
import os
from ingestion.processors import process_file

def main():
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/raw"))
    for filename in os.listdir(raw_dir):
        filepath = os.path.join(raw_dir, filename)
        try:
            print(f"Processing {filename}...")
            text = process_file(filepath)
            print(f"Output (primi 200 caratteri): {text[:200]}\n{'-'*40}\n")
        except Exception as e:
            print(f"Errore durante il processing di {filename}: {e}")

if __name__ == "__main__":
    main()
