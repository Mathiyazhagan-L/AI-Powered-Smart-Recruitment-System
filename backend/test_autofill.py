import sys
import asyncio
sys.path.insert(0, '.')

# Important: Initialize DB mapping early
import init_db
init_db.init_db()

from pathlib import Path
from fastapi import UploadFile
import io

from core.database import SessionLocal
from modules.resume_parser.service import ResumeParsingService
import modules.auth.model

async def main():
    service = ResumeParsingService()
    
    pdf_path = Path(r'C:\Recruitment\backend\modules\uploads\resumes\c11_20260609040546_resume mathi.pdf')
    print(f'Testing on {pdf_path.name}')
    
    file_bytes = pdf_path.read_bytes()
    file_obj = io.BytesIO(file_bytes)
    
    # Ensure candidate 11 exists
    with SessionLocal() as db:
        user = db.query(modules.auth.model.User).filter_by(id=11).first()
        if not user:
            user = modules.auth.model.User(id=11, email='test_autofill@example.com', role='candidate')
            db.add(user)
            db.commit()
            
    upload_file = UploadFile(filename='resume mathi.pdf', file=file_obj)
    
    with SessionLocal() as db:
        try:
            record = await service.upload_and_parse(db=db, file=upload_file, candidate_id=11)
            print('\n=== PIPELINE SUCCESS ===')
            print(f'Record ID: {record.id}')
            print(f'Parsing Status: {record.parsing_status}')
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f'\n=== PIPELINE FAILED ===')
            print(str(e))

if __name__ == '__main__':
    asyncio.run(main())
