# APT Threat Intel Pipeline

Dự án thu thập, xử lý và phân tích dữ liệu Tình báo rủi ro (Threat Intelligence) xoay quanh các chiến dịch **APT (Advanced Persistent Threat)**. 
Dữ liệu được thu thập từ nguồn mã nguồn mở (OSINT) thông qua mạng xã hội X (Twitter) và các báo cáo dạng thô (PDF, file phân tích mã độc).
Hệ thống sử dụng **MongoDB** làm cơ sở lưu trữ linh hoạt (NoSQL) và sau đó được pipeline tự động đẩy sang **Elasticsearch** (qua thư viện Python) để trực quan hóa, phân tích mạnh mẽ trên **Kibana**.

---

## 🛠 Yêu cầu Hệ thống (Prerequisites)

- **Python**: Phiên bản chuẩn từ >= `3.9`.
- **Docker & Docker Compose**: Để khởi chạy cụm Elasticsearch, Kibana, và MongoDB cục bộ một cách dễ dàng thông qua vùng chứa.

---

## 🚀 Hướng dẫn Cài đặt

### Bước 1: Clone dự án và thiết lập môi trường

Mở terminal và trỏ vào thư mục lấy code về:
```bash
cd APT_Twitter_Crawl
```

*(Khuyến nghị)* Tạo môi trường ảo (Virtual Environment) để cài đặt các package độc lập với môi trường Python hệ thống:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Cài đặt các gói thư viện Python với quy định phiên bản chính xác:
```bash
pip install -r requirements.txt
```

### Bước 2: Thiết lập Biến Môi trường (.env)

Tạo hoặc chỉnh sửa file `.env` tại thư mục gốc của dự án. 
Bạn có thể cập nhật các thông số quan trọng (vd: API Token, Host) như mẫu cấu hình đang hoạt động của hệ thống, tương tự như sau:

```env
# MongoDB Atlas hoặc Local
MONGO_URI=mongodb+srv://<db_user>:<password>@cluster0...
MONGO_DB=apt_intel
TWEETS_COLLECTION=tweets

# Twitter API Bearer Token
X_BEARER_TOKEN=<Your_Token>
TWITTER_QUERY='(#APT OR "Advanced Persistent Threat" OR "threat intel" OR #cybersecurity OR "malware analysis") lang:en -is:retweet'
TWITTER_LIMIT=2200

# Elasticsearch credentials
ELASTIC_HOST=https://localhost:9200
ELASTIC_USER=elastic
ELASTIC_PASSWORD=changeme
ELASTIC_CA_CERT=./data/certs/ca/ca.crt

ES_TWEETS_INDEX=tweets_index
ES_REPORTS_INDEX=reports_index
```

### Bước 3: Khởi động nền tảng (Database + Elastic Stack)

Chạy file Docker compose để bật đồng thời: MongoDB, Mongo-Express, Elasticsearch và Kibana.
```bash
docker compose up -d
```
Sau một vài phút khởi tạo cấu hình CA+Certificate, các docker sẽ ở trạng thái "Healthy/Running".
- **Kibana** quản trị nội dung tại: `http://localhost:5601` (User: `elastic` / Pass: `changeme`).

---

## 🔧 Cách Sử dụng Script Pipeline

Mã nguồn Python nằm tại thư mục `src/`. Có nhiều chức năng thu thập và chuẩn hoá được cung cấp:

**1. Crawler Tweet (Thu thập Intel X/Twitter)**
Kịch bản chịu trách nhiệm gọi API Twitter để fetch dữ liệu từ khóa mong muốn và lưu vào MongoDB.
```bash
python3 src/crawler_twitter.py
```

**2. Tiền xử lý & Parse file (PDF Reports)**
Nếu có những file `.pdf` chứa báo cáo APT được đưa vào `./data/raw_reports`, kịch bản sẽ dùng Apacha Tika parse text và lưu vào Mongo:
```bash
python3 src/extract_reports.py
```
*(Yêu cầu cài Java để thư viện `tika` hoạt động ngầm).*

**3. Đồng bộ Dữ liệu từ MongoDB sang Elasticsearch**
Để dữ liệu vừa crawl được đổ sang Elasticsearch thực hiện đánh chỉ mục (Index) (Làm cơ sở để Kibana truy vấn):
```bash
python3 src/index_to_elastic.py
```
> **Lưu ý:** Thư mục có khai báo chứng chỉ `ca.crt` từ volume của Docker, nên script đảm bảo được Elasticsearch bản 8.x xác thực HTTPS an toàn.

---

## 📊 Trực quan hóa dữ liệu trên Kibana

1. Truy cập [http://localhost:5601](http://localhost:5601) bằng tài khoản: `elastic` / `changeme`.
2. Truy cập thanh Menu trái -> dưới tab **Management** -> Chọn **Stack Management**.
3. Đi tới **Kibana** -> **Data Views**.
4. Tạo View Index tương ứng với `tweets_index*` (Gán timestamp alias với `@timestamp` hoặc trường `date`).
5. Vào **Discover** hoặc **Dashboards** để phân tích truy vấn KQL hoặc tạo biểu đồ theo các từ khóa như `APT`, `Russian hacker`, v.v.

---
*Môi trường hoạt động đã được kiểm định trên MacOS / ZSH Terminal.*
