from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    filename = Column(String)
    file_path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
