from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from services.file_service import validate_and_save_file
from auth.dependencies import get_current_user
from database import SessionLocal
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




def log_upload(user_id: str, filename: str):
    upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[UPLOAD LOG] User: {user_id}, File: {filename}, Time: {upload_time}")



@router.post("/api/resume/upload", tags=["Resume Upload"])
async def upload_resume(
    file: UploadFile = File(...),email_id: str = Form(...),
    current_user_email: str = Depends(get_current_user),db: Session = Depends(get_db)):
    
    if email_id != current_user_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email in token do not match!")

    success, msg = validate_and_save_file(file, email_id, db)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    log_upload(current_user_email, file.filename)

    return {"status": "success", "message": "File uploaded successfully!!!!"}
