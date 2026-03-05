"""
gfjdsgfdslkgfkdsgkfds
"""

import json
import logging
import os
import sys
import time

from utils.embeddings import generate_embeddings
from util.db import store_doc

def load_doc(file_path: str) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        docs = json.load(f)
        logging.info(f"Loaded {len(docs)} documents from {file_path}")
        return docs

def index_all_docs(docs: list[str], api_key: str) -> None:
    
    success = 0
    failed = 0
    
    
    for d, doc in enumerate(docs, start=1):
        doc_id = doc["id"]
        text = doc["text"]
        
        logging.info(f"Indexing document {d}/{len(docs)} Processing: {text[:50]}...")
        
        try:
            embedding = generate_embeddings(text, api_key) #generate embedding for this document
            stored  = store_doc({"id": doc_id, "text": text}, embedding) #store in DB
            
            if stored: 
                success += 1
                logging.info(f"Document {doc_id} indexed successfully")
            else:
                failed += 1
                logging.error(f"Failed to index document {doc_id}")
            
            
        except Exception as e:
            logging.error(f"Failed to index document {doc_id}: {e}")
            failed += 1
            continue
    
    logging.info(f"Indexing completed: {success} succeeded, {failed} failed")

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logging.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)
        
    docs_path = os.path.join(os.path.dirname(__file__), "docs.json")
    docs = load_doc(docs_path)
    
    index_all_docs(docs, api_key)
    
    logging.info("Indexing completed successfully")