from pymongo import MongoClient, ASCENDING
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "resume_parser_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

users_collection = db.users        # Users collection
resumes_collection = db.resumes    # Resumes collection
jobs_collection = db.jobs

# Create indexes for faster queries
jobs_collection.create_index([("url", ASCENDING)], unique=True)
jobs_collection.create_index([("title", ASCENDING)])
jobs_collection.create_index([("company", ASCENDING)])
jobs_collection.create_index([("location", ASCENDING)])
jobs_collection.create_index([("description_text", "text")])
      


