import os
from sqlalchemy.orm import Session
from models.resume_model import Resume
from datetime import datetime
from fastapi import UploadFile

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt", ".md")



def validate_and_save_file(file: UploadFile, email: str, db: Session):
    if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return False, "Unsupported file type!!"

    filename = f"{email.replace('@','_')}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        resume_record = Resume(
            user_email=email,
            filename=file.filename,
            file_path=file_path,
            uploaded_at=datetime.utcnow()
        )
        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)

        return True, "File saved and metadata stored", file_path



    except Exception as e:
        return False, str(e)

