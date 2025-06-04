from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from services.file_service import validate_and_save_file
from auth.dependencies import get_current_user
from database import SessionLocal
from datetime import datetime
from services.pdf_parser_service import extract_clean_text_from_pdf
from services.docx_parser_service import extract_clean_text_from_docx

from services.ollama_llm import build_resume_prompt, call_mistral
import json
from fastapi.responses import JSONResponse



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

    success, msg, file_path = validate_and_save_file(file, email_id, db)
    
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    # file_ext = file.filename.lower().split(".")[-1]
    # extracted_text = ""

    if file.filename.lower().endswith(".pdf"):
        extracted_text = extract_clean_text_from_pdf(file_path)
    elif file.filename.lower().endswith(".docx"):
        extracted_text = extract_clean_text_from_docx(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format for parsing.")
    
    
 


    log_upload(current_user_email, file.filename)
    

    prompt = build_resume_prompt(extracted_text)
    print(f"EXTRACTED TEXT ", {extracted_text})

    try:
        structured_json = call_mistral(prompt)
        parsed_output = json.loads(structured_json)  # ensure valid JSON
    except Exception as e:
      return JSONResponse(
        status_code=500,
        content={"status": "error", "message": f"LLM parsing failed: {str(e)}"}
    )

    return JSONResponse(
        status_code=200,
        content={
        "status": "success",
        "message": "File uploaded and parsed successfully",
        "Data": parsed_output
    }
)
