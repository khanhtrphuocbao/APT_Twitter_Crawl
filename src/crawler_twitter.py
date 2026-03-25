import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "apt_intel")
COLLECTION = os.getenv("TWEETS_COLLECTION", "tweets")

X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
QUERY = os.getenv("TWITTER_QUERY", '(APT OR "APT group") lang:en -is:retweet')
LIMIT = int(os.getenv("TWITTER_LIMIT", "100"))

SEARCH_URL = "https://api.x.com/2/tweets/search/recent"

if not X_BEARER_TOKEN:
    raise SystemExit("Thiếu X_BEARER_TOKEN trong .env")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
tweets_col = db[COLLECTION]

headers = {
    "Authorization": f"Bearer {X_BEARER_TOKEN}",
    "User-Agent": "apt-threat-intel/1.0"
}

def fetch_recent_posts(query: str, limit: int):
    all_docs = []
    next_token = None

    while len(all_docs) < limit:
        remaining = limit - len(all_docs)
        if remaining <= 0:
            break

        api_batch_size = max(10, min(100, remaining))

        params = {
            "query": query,
            "max_results": api_batch_size,
            "tweet.fields": "created_at,lang,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username,name"
        }
        if next_token:
            params["next_token"] = next_token

        resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=60)
        if resp.status_code != 200:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(f"X API lỗi {resp.status_code}: {detail}")

        payload = resp.json()
        data = payload.get("data", [])
        includes = payload.get("includes", {})
        users = includes.get("users", [])
        user_map = {u["id"]: u for u in users if "id" in u}

        if not data:
            break

        for tweet in data:
            author_id = tweet.get("author_id")
            user = user_map.get(author_id, {})
            username = user.get("username")
            tweet_id = tweet.get("id")
            metrics = tweet.get("public_metrics", {}) or {}

            all_docs.append({
                "tweet_id": tweet_id,
                "date": tweet.get("created_at"),
                "username": username,
                "displayname": user.get("name"),
                "content": tweet.get("text"),
                "lang": tweet.get("lang"),
                "url": f"https://x.com/{username}/status/{tweet_id}" if username and tweet_id else None,
                "reply_count": metrics.get("reply_count"),
                "retweet_count": metrics.get("retweet_count"),
                "like_count": metrics.get("like_count"),
                "quote_count": metrics.get("quote_count"),
                "source": "twitter_x_api",
                "crawled_at": datetime.utcnow()
            })

            if len(all_docs) >= limit:
                break

        next_token = payload.get("meta", {}).get("next_token")
        if not next_token:
            break

        time.sleep(1)

    return all_docs[:limit]

def save_to_mongo(docs):
    if not docs:
        print("Không có dữ liệu mới.")
        return

    ops = []
    for d in docs:
        ops.append(
            UpdateOne(
                {"tweet_id": d["tweet_id"]},
                {"$set": d},
                upsert=True
            )
        )

    result = tweets_col.bulk_write(ops, ordered=False)
    print(f"Done. matched={result.matched_count}, modified={result.modified_count}, upserted={len(result.upserted_ids)}")

if __name__ == "__main__":
    print(f"Query: {QUERY}")
    docs = fetch_recent_posts(QUERY, LIMIT)
    print(f"Fetched: {len(docs)}")
    save_to_mongo(docs)
    print("Da luu")