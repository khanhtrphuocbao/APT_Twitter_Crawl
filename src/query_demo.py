# src/query_demo.py
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

ES_HOST = os.getenv("ELASTIC_HOST", "http://localhost:9200")
ES_USER = os.getenv("ELASTIC_USER", "elastic")
ES_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme")

es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASSWORD),
    verify_certs=False
)

query = {
    "query": {
        "bool": {
            "must": [
                {"match": {"normalized_content": "APT"}}
            ],
            "must_not": [
                {"match": {"normalized_content": "APT41"}}
            ]
        }
    }
}

resp = es.search(index="tweets_index,reports_index", body=query, size=10)
for hit in resp["hits"]["hits"]:
    print(hit["_index"], hit["_score"])
    print(hit["_source"])
    print("-" * 80)