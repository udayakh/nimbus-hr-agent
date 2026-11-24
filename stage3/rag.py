from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import sys

from query import retrieve

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# The system prompt is what keeps the LLM honest: answer ONLY from the
# provided sources, cite them, and admit when the answer isn't there.
SYSTEM_PROMPT = """You are the Nimbus Notes HR assistant. You answer employee questions
using ONLY the handbook excerpts provided in each message.

Rules:
- Base your answer strictly on the excerpts. Do not use outside knowledge.
- Some excerpts may be irrelevant to the question. Ignore those.
- If the excerpts do not contain the answer, say: "I couldn't find that in the
  handbook. Please contact the People team." Do not guess.
- Be concise and friendly. Include specific numbers, limits and deadlines.
- End with "Sources:" followed by the section name(s) you actually used."""


def build_prompt(question, chunks):
    """Stuff the retrieved chunks + the question into one message."""
    context = "\n\n".join(
        f"[Excerpt {i + 1} | Section: {c['section']}]\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    return f"HANDBOOK EXCERPTS:\n{context}\n\nQUESTION: {question}"


def ask(question, n_results=5, verbose=False):
    # R — Retrieve: find relevant chunks in the vector DB
    chunks = retrieve(question, n_results=n_results)

    # A — Augment: put those chunks into the prompt
    prompt = build_prompt(question, chunks)

    # G — Generate: the LLM answers using the chunks
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,  # low = factual, consistent
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )

    if verbose:
        print("  Retrieved: " + ", ".join(f"{c['section']} ({c['score']:.2f})" for c in chunks))
        usage = response.usage_metadata
        print(f"  Tokens: {usage.prompt_token_count} in / {usage.candidates_token_count} out")
    return response.text.strip()


def chat():
    print("Nimbus Notes HR assistant. Ask about the handbook. Type 'quit' to exit.\n")
    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in ("quit", "exit", "bye"):
            break
        print(f"\nAssistant: {ask(question)}\n")


if __name__ == "__main__":
    if "--chat" in sys.argv:
        chat()
        sys.exit()

    questions = [
        "Can I buy a new monitor with company money?",   # missed in 3.5 with top-3
        "I'm having a baby in March. How much time off do I get?",
        "Can I work from Spain for two months?",
        "Does the company offer dental insurance?",        # not in the handbook
    ]
    for q in questions:
        print("=" * 70)
        print(f"Q: {q}")
        answer = ask(q, verbose=True)
        print(f"\n{answer}\n")
