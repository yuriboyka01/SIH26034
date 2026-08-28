import sys
import os
from uuid import UUID

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.inspection import Inspection
from app.core.security import create_access_token
import requests

def test():
    db = SessionLocal()
    try:
        inspection_id = '804bf9b7-79d0-4451-aa19-9de188b3cc06'
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not inspection:
            print("No such inspection")
            return
            
        print("Using user id:", inspection.created_by)
        token = create_access_token(str(inspection.created_by))
        
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = requests.post(f"http://localhost:8000/api/inspections/{inspection_id}/analyze", headers=headers)
        print("Status code:", resp.status_code)
        print("Response:", resp.text)
        
    finally:
        db.close()

if __name__ == "__main__":
    test()
