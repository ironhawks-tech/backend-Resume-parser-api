from fastapi import FastAPI
from api import upload, auth

app = FastAPI(title="Resume Parser API")


app.include_router(auth.router)
app.include_router(upload.router)
