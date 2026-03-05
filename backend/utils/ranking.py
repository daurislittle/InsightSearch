import math

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must be of the same length")
    
    #compute cosine similarity
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    #compute the magnitude of each vector
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    #guard against division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    #compute cosine similarity
    return dot_product / (magnitude1 * magnitude2)


def rank_documents(query_embedding: list[float], documents: list[dict]) -> list[dict]:
    ranked_docs = []
    for doc in documents:
        score = cosine_similarity(query_embedding, doc["embeddings"])
        ranked_docs.append({
            "id": doc["id"],
            "text": doc["text"],
            "score": score
        })
    ranked_docs.sort(key=lambda x: x["score"], reverse=True)
    return ranked_docs