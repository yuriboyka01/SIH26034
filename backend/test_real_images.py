import os
import time
import psutil
from app.ai.ocr_service import extract

def print_memory(label):
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"[{label}] Memory: {mem_mb:.2f} MB")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print_memory("Start")
    
    images_dir = "../Images"
    images = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))][:2]
    
    for img in images:
        path = os.path.join(images_dir, img)
        print(f"\n--- Testing image: {img} ---")
        
        start_t = time.time()
        res = extract(path)
        end_t = time.time()
        
        print(f"Engine: {res.engine} {res.engine_version}")
        print(f"Time: {end_t - start_t:.2f}s")
        print(f"Blocks extracted: {len(res.blocks)}")
        if res.blocks:
            print("First 3 blocks:")
            for b in res.blocks[:3]:
                print(f" - [{b.confidence:.2f}] {b.text}")
        
        print_memory(f"After {img}")
