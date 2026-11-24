from google import genai
from dotenv import load_dotenv
import math
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

EMBED_MODEL = "gemini-embedding-001"


def embed(texts):
    """Turn a list of texts into a list of vectors (lists of numbers)."""
    result = client.models.embed_content(model=EMBED_MODEL, contents=texts)
    return [e.values for e in result.embeddings]


def cosine_similarity(a, b):
    """How similar are two vectors? 1.0 = same meaning, ~0 = unrelated."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


# --- Demo 1: What does an embedding look like? ---
print("=== WHAT IS AN EMBEDDING? ===")
vector = embed(["I love pizza"])[0]
print(f"Text: 'I love pizza'")
print(f"Vector length: {len(vector)} numbers")
print(f"First 5 numbers: {[round(v, 4) for v in vector[:5]]}")
print("^ Each number captures some aspect of the meaning.\n")


# --- Demo 2: Similar meaning = similar vectors ---
# Notice: the best matches share MEANING, not necessarily WORDS.
print("=== SEMANTIC SEARCH ===")
documents = [
    "How do I reset my password?",
    "I forgot my login credentials",
    "The weather is sunny today",
    "What's the best pizza topping?",
    "My account is locked and I can't sign in",
]
query = "I can't log into my account"

doc_vectors = embed(documents)
query_vector = embed([query])[0]

scores = [(cosine_similarity(query_vector, dv), doc) for dv, doc in zip(doc_vectors, documents)]
scores.sort(reverse=True)

print(f"Query: '{query}'\n")
for score, doc in scores:
    bar = "#" * int(score * 30)
    print(f"{score:.3f}  {bar:<30}  {doc}")

print("\n^ This ranking is exactly what RAG does to find relevant chunks!")
