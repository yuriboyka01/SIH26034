import psutil
import os
import time

def get_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def print_memory(label):
    print(f"{label}: {get_memory_mb():.2f} MB")

if __name__ == "__main__":
    print_memory("Initial memory")
    
    # Simulate loading environment
    from dotenv import load_dotenv
    load_dotenv()
    
    print_memory("After dotenv")
    
    from app.ai.ocr_service import _get_ocr
    print_memory("After importing OCR service module")
    
    start_time = time.time()
    instance, version, engine_name = _get_ocr()
    init_time = time.time() - start_time
    print_memory(f"After _get_ocr() initialization (took {init_time:.2f}s)")
    
    # Run dummy inference to force full lazy loading
    import numpy as np
    import cv2
    img = np.zeros((800, 600, 3), dtype=np.uint8)
    
    start_time = time.time()
    res = instance.ocr(img, cls=True)
    infer_time = time.time() - start_time
    print_memory(f"After dummy inference (took {infer_time:.2f}s)")
    
    # Sleep a bit and force GC to see if memory is released
    import gc
    gc.collect()
    print_memory("After forced garbage collection")
