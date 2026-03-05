import json
import logging
import os

from utils.embeddings import generate_embeddings, get_api_key
from utils.db import get_all_documents
from utils.ranking import rank_documents

API_KEY_CACHED = None

def get_api_key_cached() -> str:
    global API_KEY_CACHED
    
    if API_KEY_CACHED is None:
        API_KEY_CACHED = get_api_key()
    return API_KEY_CACHED

def build_response(res: dict, status_code: int) -> dict:
    return {
        "statusCode": status_code,
        "body": json.dumps(res)
    }
    
    
def parse_query(event: dict) -> str:
    try:
        body = json.loads(event.get("body", "{}"))
        query = body.get("query", "")
        
        if not query:
            logging.error("Query is missing")
            raise ValueError("Query is missing")
        
        if len(query) > 500:
            logging.error("Query is too long")
            raise ValueError("Query is too long")
        
        return query
    except (json.JSONDecodeError, ValueError) as e:
        logging.error(f"Invalid request: {e}")
        raise ValueError(f"Invalid request: {e}")
    
def lambda_handler(event, context) -> dict:
        
    logging.info(f"Lambda function invoked with event: {json.dumps(event)}")
    
    if event.get("httpMethod") == "OPTIONS":
        return build_response({"message":"OK"}, 200)
    
    try:
        query = parse_query(event)
        logging.info(f"Processing query: {query}")
        
        api_key = get_api_key_cached()
        
        embeddings = generate_embeddings(query, api_key)
        logging.info(f"Generated embeddings for query: {len(embeddings)}")
        
        documents = get_all_documents()
        if not documents:
            return build_response({"query": query, "results": [], "message": "No documents found"}, 200)
        
        results = rank_documents(embeddings, documents)
        
        
        response_body = {
            "query": query, 
            "total_documents_searched": len(documents),
            "total_results_returned": len(results),
            "results": results
        }
        logging.info(f"Returning {len(results)} results for query: {query}")
        return build_response(response_body, 200)
    except ValueError as e:
        logging.error(f"ValueError: {e}")
        return build_response({"error": str(e)}, 400)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return build_response({"error": "Internal server error"}, 500)