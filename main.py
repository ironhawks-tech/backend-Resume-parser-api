from fastapi import FastAPI
from api import upload, auth
from database import Base, engine 


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Resume Parser API")


app.include_router(auth.router)
app.include_router(upload.router)
