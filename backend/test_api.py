import sys
import os
from uuid import UUID

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.repositories.inspection_repository import InspectionRepository
from app.services.analysis_service import AnalysisService

def test():
    db = SessionLocal()
    try:
        repo = InspectionRepository(db)
        inspection_id = UUID('804bf9b7-79d0-4451-aa19-9de188b3cc06')
        inspection = repo.get_by_id(inspection_id)
        if not inspection:
            print("Inspection not found!")
            return
            
        print(f"Found inspection, created by user: {inspection.created_by}")
        
        svc = AnalysisService(db)
        result = svc.analyze_inspection(inspection_id, inspection.created_by)
        print("Success:", result)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
