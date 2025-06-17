from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "resume_parser_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

users_collection = db.users        # Users collection
resumes_collection = db.resumes    # Resumes collection
      
jobs_collection = db.jobs          # Job listings
user_searches_collection = db.user_searches 
