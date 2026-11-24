from google import genai
from dotenv import load_dotenv
import chromadb
import os

load_dotenv()

gemini = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
EMBED_MODEL = "gemini-embedding-001"


def embed(texts):
    """Same helper as 3.1: texts -> vectors, using Gemini."""
    result = gemini.models.embed_content(model=EMBED_MODEL, contents=texts)
    return [e.values for e in result.embeddings]


# --- Step 1: Create a client ---
# PersistentClient saves everything to a folder on disk,
# so your data is still there the next time you run the script.
db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
client = chromadb.PersistentClient(path=db_path)

# --- Step 2: Create (or open) a collection ---
# A collection is like a table. "cosine" = use the same similarity math as 3.1.
# embedding_function=None -> we supply our own Gemini embeddings.
collection = client.get_or_create_collection(
    name="support_faq",
    embedding_function=None,
    configuration={"hnsw": {"space": "cosine"}},
)

# --- Step 3: Add documents (only if the collection is empty) ---
documents = [
    "How do I reset my password?",
    "I forgot my login credentials",
    "The weather is sunny today",
    "What's the best pizza topping?",
    "My account is locked and I can't sign in",
    "Our office is open Monday to Friday, 9am to 5pm",
    "Refunds are processed within 5 business days",
]
metadatas = [
    {"category": "account"},
    {"category": "account"},
    {"category": "chitchat"},
    {"category": "chitchat"},
    {"category": "account"},
    {"category": "info"},
    {"category": "billing"},
]

if collection.count() == 0:
    print("Collection is empty -> embedding and saving documents...")
    collection.add(
        ids=[f"doc{i}" for i in range(len(documents))],
        documents=documents,
        embeddings=embed(documents),
        metadatas=metadatas,
    )
else:
    print("Collection already has data on disk -> skipping embedding (no API cost!)")

print(f"Documents stored: {collection.count()}\n")

# --- Step 4: Query by meaning ---
def search(question, n=3, where=None):
    results = collection.query(
        query_embeddings=embed([question]),
        n_results=n,
        where=where,  # optional metadata filter
    )
    print(f"Q: {question}" + (f"   (filter: {where})" if where else ""))
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        # distance = 1 - similarity, so smaller = closer
        print(f"  {1 - dist:.3f}  [{meta['category']}]  {doc}")
    print()


print("=== SEARCH ===")
search("I can't log into my account")
search("When will I get my money back?")
search("What time do you open?", n=2)

print("=== SEARCH WITH METADATA FILTER ===")
search("I can't log into my account", where={"category": "billing"})
