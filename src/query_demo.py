# src/query_demo.py
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

ES_HOST = os.getenv("ELASTIC_HOST", "https://localhost:9200")
ES_USER = os.getenv("ELASTIC_USER", "elastic")
ES_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme")

es = Elasticsearch(
    ES_HOST,
    ca_certs="./data/certs/ca/ca.crt",
    basic_auth=(ES_USER, ES_PASSWORD),
    verify_certs=True
)

query = {
    "query": {
    "bool": {
        "must": [{"match": {"content": "APT"}}],
        "should": [
            {"match": {"content": "malware"}},
            {"match": {"content": "attack"}},
            {"match": {"content": "threat"}},
        ],
        "minimum_should_match": 1
    }
}
}

resp = es.search(index="tweets_index,reports_index", body=query, size=10)
for hit in resp["hits"]["hits"]:
    print(hit["_index"], hit["_score"])
    print(hit["_source"])
    print("-" * 80)