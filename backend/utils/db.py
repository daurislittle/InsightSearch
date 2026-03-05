import json
import logging
import boto3
from boto3.dynamodb.conditions import Key 
from botocore.exceptions import ClientError

TABLE_NAME = "searchable-documents"
REGION = "us-east-1"

def get_table():
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
    return table

def store_document(doc_id: str, text: str, embeddings: list[float]):
    
    table = get_table()
    try:
        item = {
            "id": doc_id,
            "text": text,
            "embeddings": json.dumps(embeddings)
        }
        
        table.put_item(
            Item=item
        )
        
        logging.info(f"Stored document {doc_id} in DynamoDB")
        return True
    except ClientError as e:
        logging.error(f"Failed to store document: {doc_id} in DynamoDB: {e}")
        return False

def get_all_documents() -> list[dict]:
    
    table = get_table()
    documents = []
    
    try:
        res = table.scan()
        items = res.get("Items", [])
        
        while 'LastEvaluatedKey' in res:
            res = table.scan(ExclusiveStartKey=res['LastEvaluatedKey'])
            items.extend(res.get("Items", []))
            
        for i in items:
            documents.append({
                "id": i["id"],
                "text": i["text"],
                "embeddings": json.loads(i["embeddings"])
            })
            
        logging.info(f"Retrieved {len(documents)} documents from DynamoDB")
        return documents
    except ClientError as e:
        logging.error(f"Failed to retrieve documents from DynamoDB: {e}")
        return []
