import sys
import os
import json

# Add backend dir to python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.ai.extraction import extract_product_info

def test_llm():
    blocks = [
        { "text": "Brand: TestBrand", "confidence": 0.99, "bbox": [0,0,10,10] },
        { "text": "MRP: Rs 499.00", "confidence": 0.98, "bbox": [0,10,10,20] },
        { "text": "Manufactured Date: 01/01/2026", "confidence": 0.95, "bbox": [0,20,10,30] },
        { "text": "Net Wt 500g", "confidence": 0.90, "bbox": [0,30,10,40] },
        { "text": "Ingredients: Water, Sugar, Salt", "confidence": 0.90, "bbox": [0,40,10,50] },
        { "text": "Storage: Keep in a cool dry place", "confidence": 0.88, "bbox": [0,50,10,60] },
        { "text": "Unit Sale Price: Rs 1.00 per g", "confidence": 0.91, "bbox": [0,60,10,70] }
    ]
    
    print("Running LLM extraction...")
    result = extract_product_info(blocks)
    
    print(f"Extraction Version Used: {result.extraction_version}")
    print(json.dumps(result.to_dict(), indent=2))

if __name__ == "__main__":
    test_llm()
