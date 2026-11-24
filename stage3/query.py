import sys

from embedder import embed
from ingest import get_collection

collection = get_collection()


def retrieve(question, n_results=3, section=None):
    """Find the chunks most relevant to a question.

    Returns a list of dicts: text, section, source, score (1.0 = perfect match).
    """
    # Questions use RETRIEVAL_QUERY (chunks were stored with RETRIEVAL_DOCUMENT)
    query_vector = embed([question], task_type="RETRIEVAL_QUERY")
    results = collection.query(
        query_embeddings=query_vector,
        n_results=n_results,
        where={"section": section} if section else None,
    )
    return [
        {
            "text": doc,
            "section": meta["section"],
            "source": meta["source"],
            "score": 1 - dist,  # Chroma returns distance; flip it to similarity
        }
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        )
    ]


def show(question, **kwargs):
    print(f"\nQ: {question}" + (f"   {kwargs}" if kwargs else ""))
    for r in retrieve(question, **kwargs):
        preview = r["text"].replace("\n", " ")[:85]
        print(f"  {r['score']:.3f}  [{r['section']}]  {preview}...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Ask your own question:  python stage3/query.py "your question here"
        show(" ".join(sys.argv[1:]))
        sys.exit()

    print("=== 1. QUESTIONS THE HANDBOOK ANSWERS ===")
    show("How many vacation days do I get?")
    show("Can I buy a new monitor with company money?")
    show("I lost my laptop, what should I do?")

    print("\n=== 2. DIFFERENT WORDS, SAME MEANING ===")
    show("I'm having a baby soon")        # handbook says "parental leave"
    show("I feel burned out and need a day off")  # handbook says "mental health days"

    print("\n=== 3. A QUESTION THE HANDBOOK CAN'T ANSWER ===")
    show("Does the company offer dental insurance?")

    print("\n=== 4. FILTER BY SECTION ===")
    show("How much money do I get?", section="Learning and Development")
