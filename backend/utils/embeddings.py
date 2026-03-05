import json 
import boto3
from botocore.exceptions import ClientError

def get_api_key(secret_name: str, region_name: str) -> str:
    
    client = boto3.client("secretsmanager", region_name=region_name)
    
    try:
        pass
    except ClientError as e:
        raise e
    
def generate_embeddings(text: str, api_key: str) -> list[float]:
    pass

