import json
import logging 
import boto3
from botocore.exceptions import ClientError

def get_api_key(secret_name: str, region_name: str) -> str:
    
    client = boto3.client("secretsmanager", region_name=region_name)
    
    try:
        res = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(res.get("SecretString"))
        return secret.get("OPENAI_API_KEY")
    except ClientError as e:
        logging.error(f"Failed to retrieve API key from Secrets Manager: {e}")
        raise e
    
def generate_embeddings(text: str, api_key: str) -> list[float]:
    if not text or not text.strip():
        logging.error("Text is empty or None")
        raise ValueError("Text is empty or None")
    
    text = text.strip()[:8000]
    client = openai.OpenAI(api_key=api_key)
    
    try:
        res = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
         
        embedding = res.data[0].embedding
         
        # Check if the embedding is valid
        if not embedding or len(embedding) == 0:
            raise ValueError("Failed to generate embeddings: empty result")
         
        logging.info(f"Generated embeddings for text: {len(embedding)}")
        return embedding
    except openai.OpenAIError as e:
        logging.error(f"Failed to generate embeddings: {e}")
        raise e
    

