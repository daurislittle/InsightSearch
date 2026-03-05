import json
import boto3
from boto3.dynamodb.conditions import Key 
from botocore.exceptions import ClientError

def get_table():
    pass

def store_document(doc_id: str, text: str, embeddings: list[float]):
    pass

def get_all_documents() -> list[dict]:
    pass

