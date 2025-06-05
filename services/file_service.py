import os
from fastapi import UploadFile
from datetime import datetime
from database import resumes_collection  # MongoDB collection

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt", ".md")

def validate_and_save_file(file: UploadFile, email: str):
    if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return False, "Unsupported file type!!", None

    filename = f"{email.replace('@', '_')}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # Insert resume metadata into MongoDB
        resumes_collection.insert_one({
            "user_email": email,
            "filename": file.filename,
            "file_path": file_path,
            "uploaded_at": datetime.utcnow()
        })

        return True, "File saved and metadata stored", file_path

    except Exception as e:
        return False, str(e), None
