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

    parsed = parser.from_file(path)
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

class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            time.sleep(1)
            process_pdf(event.src_path)

if __name__ == "__main__":
    # xử lý file cũ trước
    for fname in os.listdir(REPORTS_DIR):
        process_pdf(os.path.join(REPORTS_DIR, fname))

    observer = Observer()
    observer.schedule(PDFHandler(), REPORTS_DIR, recursive=False)
    observer.start()
    print("Watching folder for new PDF files...")

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()