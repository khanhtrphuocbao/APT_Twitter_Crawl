# src/crawler_vxug.py
import os
import hashlib
import threading
import requests
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor

# Đổi sang nguồn mở blackorbird/APT_REPORT trên Github
API_URL = "https://api.github.com/repos/blackorbird/APT_REPORT/git/trees/master?recursive=1"
REPORTS_DIR = os.getenv("REPORTS_DIR", "./data/raw_reports")
DOWNLOADED_LOG = os.getenv("DOWNLOADED_LOG", "./data/logs/downloaded_reports.txt")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DOWNLOADED_LOG), exist_ok=True)

log_lock = threading.Lock()

def load_downloaded():
    if not os.path.exists(DOWNLOADED_LOG):
        return set()
    with open(DOWNLOADED_LOG, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

DOWNLOADED_FILES = load_downloaded()

def append_log(url):
    with log_lock:
        with open(DOWNLOADED_LOG, "a", encoding="utf-8") as f:
            f.write(url + "\n")
        DOWNLOADED_FILES.add(url)

def get_pdf_links(api_url):
    # Lấy danh sách file dưới dạng JSON tử Github Tree API (Cào đệ quy toàn bộ thư mục)
    resp = requests.get(api_url, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("tree", [])

    links = []
    base_download_url = "https://raw.githubusercontent.com/blackorbird/APT_REPORT/master/"
    
    from urllib.parse import quote
    for item in data:
        path = item.get("path", "")
        if item.get("type") == "blob" and path.lower().endswith(".pdf"):
            # Nối URL tải thủ công vì Tree API không trả về download_url
            dl_url = base_download_url + quote(path)
            links.append(dl_url)
            # Giới hạn Demo 15 file cho quá trình chạy nhanh.
            if len(links) >= 15:
                break
    return list(set(links))

def download_pdf(pdf_url):
    if not pdf_url: return "skip empty"
    if pdf_url in DOWNLOADED_FILES:
        filename = unquote(pdf_url.split("/")[-1])
        return f"skip {filename}"

    try:
        resp = requests.get(pdf_url, timeout=60)
        resp.raise_for_status()

        filename = pdf_url.split("/")[-1] or hashlib.md5(pdf_url.encode()).hexdigest() + ".pdf"
        filename = unquote(filename) # Format lại tên cho dễ nhìn
        path = os.path.join(REPORTS_DIR, filename)

        with open(path, "wb") as f:
            f.write(resp.content)

        append_log(pdf_url)
        return f"ok {filename}"
    except Exception as e:
        return f"fail {pdf_url}: {e}"

if __name__ == "__main__":
    print("[1] Fetching PDF links from APTNotes Github Repository...")
    pdf_links = get_pdf_links(API_URL)
    print(f"[2] Found {len(pdf_links)} reports. Starting multi-thread download...\n")

    with ThreadPoolExecutor(max_workers=5) as ex:
        for r in ex.map(download_pdf, pdf_links):
            print(r)