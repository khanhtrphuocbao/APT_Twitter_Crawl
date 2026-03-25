# src/crawler_vxug.py
import os
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://vx-underground.org/"   # chỉnh lại đúng chuyên mục nếu cần
REPORTS_DIR = os.getenv("REPORTS_DIR", "./data/raw_reports")
DOWNLOADED_LOG = os.getenv("DOWNLOADED_LOG", "./data/logs/downloaded_reports.txt")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DOWNLOADED_LOG), exist_ok=True)

def load_downloaded():
    if not os.path.exists(DOWNLOADED_LOG):
        return set()
    with open(DOWNLOADED_LOG, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def append_log(url):
    with open(DOWNLOADED_LOG, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def get_pdf_links(page_url):
    resp = requests.get(page_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            links.append(urljoin(page_url, href))
    return list(set(links))

def download_pdf(pdf_url):
    downloaded = load_downloaded()
    if pdf_url in downloaded:
        return f"skip {pdf_url}"

    try:
        resp = requests.get(pdf_url, timeout=60)
        resp.raise_for_status()

        filename = pdf_url.split("/")[-1] or hashlib.md5(pdf_url.encode()).hexdigest() + ".pdf"
        path = os.path.join(REPORTS_DIR, filename)

        with open(path, "wb") as f:
            f.write(resp.content)

        append_log(pdf_url)
        return f"ok {filename}"
    except Exception as e:
        return f"fail {pdf_url}: {e}"

if __name__ == "__main__":
    # demo: lấy 1 trang, nếu muốn spider nhiều trang thì mở rộng thêm while/page loop
    page_url = BASE_URL
    pdf_links = get_pdf_links(page_url)

    with ThreadPoolExecutor(max_workers=8) as ex:
        for r in ex.map(download_pdf, pdf_links):
            print(r)