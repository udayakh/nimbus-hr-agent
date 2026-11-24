"""Lesson 6.1: one HR agent that combines RAG (Stage 3) and tools (Stage 4)."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "stage3"))  # retrieve() : Gemini embeddings + ChromaDB
sys.path.insert(0, str(ROOT / "stage4"))  # tool loop + HR tools (Ollama)

from query import retrieve  # noqa: E402
from multiple_tools import check_vacation_balance, request_time_off  # noqa: E402
from tool_loop import run, MODEL  # noqa: E402


# =====================================================================
# RAG AS A TOOL
# In Stage 3, retrieval ran on EVERY question. Now it's just one tool:
# the agent decides WHEN it needs to look something up in the handbook.
# =====================================================================
def search_handbook(question: str) -> dict:
    """Search the company employee handbook for POLICIES and RULES: vacation allowance,
    carry-over, sick leave, parental leave, remote work, home office budget, expenses,
    learning budget, laptops, performance reviews.

    Args:
        question: What to look up, e.g. "how many vacation days can be carried over".
    """
    chunks = retrieve(str(question), n_results=3)
    return {"excerpts": [{"section": c["section"], "text": c["text"]} for c in chunks]}


TOOLS = [search_handbook, check_vacation_balance, request_time_off]

SYSTEM_PROMPT = """You are the Nimbus Notes HR assistant.

Pick the right tool:
- Questions about company POLICY or RULES -> search_handbook
- A specific person's remaining vacation days -> check_vacation_balance
- Booking time off for someone -> request_time_off (only when clearly asked to book)
- A question may need more than one tool. Call each one you need.

Rules:
- Answer only from tool results. Never invent numbers or policies.
- If the handbook excerpts don't contain the answer, say so.
- Mention the handbook section when you used search_handbook.
- If a question has nothing to do with HR, answer briefly without tools."""

QUESTIONS = [
    "How many vacation days do employees get per year?",           # RAG
    "How many vacation days does Priya have left?",                # live data
    "What is the home office budget for new employees?",           # RAG
    "Please book 2 days off for Marco starting 2026-12-29.",       # action
    "How many vacation days does Priya have left, and how many of them "
    "can she carry over into next year?",                          # RAG + live data
    "What's the capital of France?",                               # no tool
]


if __name__ == "__main__":
    print(f"Chat model: {MODEL} (Ollama)  |  Embeddings: Gemini  |  Vector DB: ChromaDB")
    for q in QUESTIONS:
        print("\n" + "=" * 70)
        print(f"Q: {q}")
        answer = run(q, TOOLS, SYSTEM_PROMPT)
        print(f"A: {answer}")
