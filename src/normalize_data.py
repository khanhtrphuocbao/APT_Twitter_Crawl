# src/normalize_data.py
import os
import re
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
TWEETS_COLLECTION = os.getenv("TWEETS_COLLECTION", "tweets")
REPORTS_COLLECTION = os.getenv("REPORTS_COLLECTION", "reports")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

tweets_col = db[TWEETS_COLLECTION]
reports_col = db[REPORTS_COLLECTION]

def normalize_tweet(text: str) -> str:
    if not text:
        return ""
    # giữ hashtag, URL, chữ số, chữ cái, khoảng trắng, một số dấu cơ bản
    text = re.sub(r"[^\w\s#:/\.\-\_\?\=&]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_report(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_collection():
    for doc in tweets_col.find({}, {"content": 1}):
        norm = normalize_tweet(doc.get("content", ""))
        tweets_col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"normalized_content": norm}}
        )

    for doc in reports_col.find({}, {"content": 1}):
        norm = normalize_report(doc.get("content", ""))
        reports_col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"normalized_content": norm}}
        )

if __name__ == "__main__":
    normalize_collection()
    print("Normalized content updated.")