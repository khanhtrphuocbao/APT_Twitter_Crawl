# src/index_to_elastic.py
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
from elasticsearch import Elasticsearch, helpers

load_dotenv(override=True)

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
TWEETS_COLLECTION = os.getenv("TWEETS_COLLECTION", "tweets")
REPORTS_COLLECTION = os.getenv("REPORTS_COLLECTION", "reports")

ES_HOST = os.getenv("ELASTIC_HOST", "https://localhost:9200")
ES_USER = os.getenv("ELASTIC_USER", "elastic")
ES_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme")
ES_TWEETS_INDEX = os.getenv("ES_TWEETS_INDEX", "tweets_index")
ES_REPORTS_INDEX = os.getenv("ES_REPORTS_INDEX", "reports_index")

mongo = MongoClient(MONGO_URI)
db = mongo[MONGO_DB]

es = Elasticsearch(
    ES_HOST,
    ca_certs="./data/certs/ca/ca.crt",
    basic_auth=(ES_USER, ES_PASSWORD),
    verify_certs=True,
    node_class="requests"
)

tweets_mapping = {
    "mappings": {
        "properties": {
            "tweet_id": {"type": "keyword"},
            "date": {"type": "date"},
            "username": {"type": "keyword"},
            "displayname": {"type": "text"},
            "content": {"type": "text"},
            "normalized_content": {"type": "text"},
            "url": {"type": "keyword"},
            "source": {"type": "keyword"}
        }
    }
}

reports_mapping = {
    "mappings": {
        "properties": {
            "file_name": {"type": "keyword"},
            "file_path": {"type": "keyword"},
            "file_hash": {"type": "keyword"},
            "content": {"type": "text"},
            "normalized_content": {"type": "text"},
            "source": {"type": "keyword"},
            "indexed_at": {"type": "date"}
        }
    }
}

def create_index_if_not_exists(index_name, mapping):
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=mapping)

def bulk_index_tweets():
    docs = db[TWEETS_COLLECTION].find()
    def generate_actions():
        for doc in docs:
            yield {
                "_index": ES_TWEETS_INDEX,
                "_id": str(doc["_id"]),
                "_source": {
                    "tweet_id": doc.get("tweet_id"),
                    "date": doc.get("date"),
                    "username": doc.get("username"),
                    "displayname": doc.get("displayname"),
                    "content": doc.get("content"),
                    "normalized_content": doc.get("normalized_content"),
                    "url": doc.get("url"),
                    "source": doc.get("source")
                }
            }
    helpers.bulk(es, generate_actions())

def bulk_index_reports():
    docs = db[REPORTS_COLLECTION].find()
    def generate_actions():
        for doc in docs:
            yield {
                "_index": ES_REPORTS_INDEX,
                "_id": str(doc["_id"]),
                "_source": {
                    "file_name": doc.get("file_name"),
                    "file_path": doc.get("file_path"),
                    "file_hash": doc.get("file_hash"),
                    "content": doc.get("content"),
                    "normalized_content": doc.get("normalized_content"),
                    "source": doc.get("source"),
                    "indexed_at": datetime.now(timezone.utc).isoformat()
                }
            }
    helpers.bulk(es, generate_actions())

if __name__ == "__main__":
    create_index_if_not_exists(ES_TWEETS_INDEX, tweets_mapping)
    create_index_if_not_exists(ES_REPORTS_INDEX, reports_mapping)

    bulk_index_tweets()
    bulk_index_reports()

    print("Indexing completed.")