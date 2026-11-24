from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
EMBED_MODEL = "gemini-embedding-001"
BATCH_SIZE = 100  # the API accepts at most 100 texts per request


def embed(texts, task_type="RETRIEVAL_DOCUMENT"):
    """Turn texts into vectors.

    task_type tells Gemini how the vector will be used:
      - "RETRIEVAL_DOCUMENT" for chunks you store in the database
      - "RETRIEVAL_QUERY"    for the user's question at search time
    Using the right one on each side gives better search results.
    """
    vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        result = _client.models.embed_content(
            model=EMBED_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        vectors.extend(e.values for e in result.embeddings)
    return vectors
