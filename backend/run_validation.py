import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.ai.ocr_service import extract
from app.ai.extraction import extract_product_info

IMAGES_DIR = Path(r"D:\SIH26034\Images")

images = [
    ("Moksh Agarbatti", "Agarbatti_back.jpeg"),
    ("Gold Winner Refined Sunflower Oil", "GOLD_back.jpeg"),
    ("Sunraja Gulas Jaggery Powder", "GULAS_back.jpeg"),
    ("Tata Tea Chakra Gold", "chakrabackend.jpeg"),
]

def main():
    results = {}
    for product_name, filename in images:
        image_path = IMAGES_DIR / filename
        print(f"Processing {product_name} ({filename})...")
        
        try:
            # 1. OCR
            ocr_result = extract(str(image_path))
            blocks = []
            for b in ocr_result.blocks:
                blocks.append({
                    "text": b.raw_text,
                    "normalized_text": b.normalized_text,
                    "confidence": b.confidence,
                    "bbox": b.bbox,
                })
            
            print(f"  OCR extracted {len(blocks)} blocks.")
            
            # 2. Extraction
            structured_data = extract_product_info(blocks, inspection_product_name=product_name)
            
            # Record
            results[product_name] = {
                "ocr_blocks_count": len(blocks),
                "ocr_blocks": blocks,
                "extracted_fields": [
                    {
                        "field_name": getattr(f, "field_name", ""),
                        "value": getattr(f, "value", None),
                        "detection_status": getattr(f, "detection_status", ""),
                        "evidence": f.evidence.__dict__ if getattr(f, "evidence", None) else None
                    }
                    for f in structured_data.fields
                ] if hasattr(structured_data, "fields") else []
            }
        except Exception as e:
            import traceback
            print(f"  Failed: {e}")
            traceback.print_exc()
            results[product_name] = {"error": str(e)}
            
    with open("validation_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
