from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from database import users_collection
from auth.utils import hash_password, verify_password, authenticate_user
from auth.jwt import create_access_token
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
@router.post("/auth/register", status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register(user: UserCreate):
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    new_user_doc = {
        "email": user.email,
        "hashed_password": hashed_pw
    }
    insert_result = users_collection.insert_one(new_user_doc)
    if not insert_result.inserted_id:
        raise HTTPException(status_code=500, detail="User registration failed")

    return {"msg": "User registered successfully!!!"}

@router.post("/auth/token", tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password

    user_doc = users_collection.find_one({"email": email})
    if not user_doc or not verify_password(password, user_doc["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}
