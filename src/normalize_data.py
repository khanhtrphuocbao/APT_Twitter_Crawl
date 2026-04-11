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
    """Chuẩn hóa nội dung tweet - giữ nguyên hashtag và URL, xóa emoji/ký tự điều khiển."""
    if not text:
        return ""
    # Xóa ký tự điều khiển Unicode (nhưng giữ emoji and tiếng nước ngoài)
    text = re.sub(r"[\x00-\x1F\x7F]", " ", text)
    # Xóa URL rút gọn (t.co) và URL thô để giảm nhiễu
    text = re.sub(r"https?://\S+", "", text)
    # Xóa mention @username
    text = re.sub(r"@\w+", "", text)
    # Xóa ký tự $ (dấu tiền - thường dùng cho token crypto như $APT)
    text = re.sub(r"\$[A-Z]+", "", text)
    # Gộp khoảng trắng thừa
    text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_report(text: str) -> str:
    """Chuẩn hóa nội dung báo cáo PDF - xóa ký tự thừa và ký tự điều khiển."""
    if not text:
        return ""
    # Xóa ký tự form-feed (\f) và ký tự điều khiển PDF thường gặp
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", text)
    # Xóa soft-hyphen (U+00AD) thường xuất hiện khi PDF xuống dòng
    text = text.replace("\u00ad", "")
    # Gộp nhiều dòng trắng liên tiếp thành 1 dòng xuống
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Gộp khoảng trắng thừa trên cùng 1 dòng
    text = re.sub(r"[^\S\n]+", " ", text)
    return text.strip()

def normalize_collection():
    from pymongo import UpdateOne
    
    tweet_ops = []
    for doc in tweets_col.find({}, {"content": 1}):
        norm = normalize_tweet(doc.get("content", ""))
        tweet_ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": {"normalized_content": norm}}))
    if tweet_ops:
        tweets_col.bulk_write(tweet_ops, ordered=False)

    report_ops = []
    for doc in reports_col.find({}, {"content": 1}):
        norm = normalize_report(doc.get("content", ""))
        report_ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": {"normalized_content": norm}}))
    if report_ops:
        reports_col.bulk_write(report_ops, ordered=False)

if __name__ == "__main__":
    normalize_collection()
    print("Normalized content updated.")