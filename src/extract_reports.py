# src/extract_reports.py
import os
import time
import hashlib
from dotenv import load_dotenv
from pymongo import MongoClient
from tika import parser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
REPORTS_COLLECTION = os.getenv("REPORTS_COLLECTION", "reports")
REPORTS_DIR = os.getenv("REPORTS_DIR", "./data/raw_reports")
PROCESSED_LOG = os.getenv("PROCESSED_LOG", "./data/logs/processed_reports.txt")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
reports_col = db[REPORTS_COLLECTION]

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROCESSED_LOG), exist_ok=True)

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_processed():
    if not os.path.exists(PROCESSED_LOG):
        return set()
    with open(PROCESSED_LOG, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def append_processed(file_hash_value):
    with open(PROCESSED_LOG, "a", encoding="utf-8") as f:
        f.write(file_hash_value + "\n")

def process_pdf(path):
    if not path.lower().endswith(".pdf"):
        return

    h = file_hash(path)
    if h in load_processed():
        print(f"Already processed: {path}")
        return

    try:
        # Tăng timeout lên 300 giây để tránh bị văng với các file PDF cực kỳ nặng
        parsed = parser.from_file(path, requestOptions={'timeout': 300})
        content = parsed.get("content", "") or ""
        metadata = parsed.get("metadata", {}) or {}

        doc = {
            "file_name": os.path.basename(path),
            "file_path": os.path.abspath(path),
            "file_hash": h,
            "content": content,
            "metadata": metadata,
            "source": "vxug_report"
        }
        reports_col.insert_one(doc)
        append_processed(h)
        print(f"Inserted report: {path}")
    except Exception as e:
        print(f"Error parsing {path}: {e}")

if __name__ == "__main__":
    print(f"Bắt đầu trích xuất Text từ các file PDF trong thư mục {REPORTS_DIR}...")
    
    # Lấy danh sách tất cả file trong thư mục
    files = [f for f in os.listdir(REPORTS_DIR) if f.lower().endswith('.pdf')]
    print(f"Tìm thấy {len(files)} file PDF để xử lý.")
    
    for fname in files:
        process_pdf(os.path.join(REPORTS_DIR, fname))
        
    print("Hoàn thành trích xuất tất cả các báo cáo PDF!")