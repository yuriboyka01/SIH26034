import sys
import os
from uuid import UUID

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.analysis_service import AnalysisService
from app.core.config import settings

def test():
    db = SessionLocal()
    try:
        svc = AnalysisService(db)
        
        from app.models.inspection import Inspection
        from app.models.inspection_image import InspectionImage
        inspection = db.query(Inspection).filter(Inspection.id == '804bf9b7-79d0-4451-aa19-9de188b3cc06').first()
        image = db.query(InspectionImage).filter(InspectionImage.inspection_id == '804bf9b7-79d0-4451-aa19-9de188b3cc06').first()
        if not image:
            print("No image")
            return
            
        # Patch the file path to exist
        image.file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads", image.stored_filename)
        print("Patched path:", image.file_path)
        
        result = svc._analyze_image(image, inspection)
        print("SUCCESS IN PYTHON!")
        
        # Test pydantic validation
        from app.schemas.analysis import ImageAnalysisResult
        validated = ImageAnalysisResult(**result)
        print("PYDANTIC SUCCESS!")
        
    except Exception as e:
        print("EXCEPTION")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
