import sys
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ValidationError

# Reuse the Ollama helper from Stage 4
sys.path.insert(0, str(Path(__file__).parent.parent / "stage4"))
from tool_loop import chat, MODEL  # noqa: E402


def llm(prompt, system="You are a helpful assistant.", schema=None):
    """One LLM call. Pass a pydantic model as `schema` to force JSON output."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    response = chat(messages, format=schema.model_json_schema() if schema else None)
    return response.message.content.strip()


# =====================================================================
# The input: a messy, real-world customer email
# =====================================================================
EMAIL = """hi there,, so I ordered the blue backpack (order #A-48213) on the 3rd and
its now the 19th and NOTHING. tracking hasnt updated in a week. honestly
pretty annoyed, this was meant to be a birthday gift for my son which was
yesterday. i dont want a replacement at this point i just want my money back.
- Dana"""

POLICY = "Orders not delivered within 10 days of purchase get a full refund, processed within 5 business days."


# =====================================================================
# STEP 1: EXTRACT. Turn messy text into clean, structured facts.
# The schema tells the LLM exactly which fields to fill in.
# =====================================================================
class EmailFacts(BaseModel):
    customer_name: str
    order_id: Optional[str]
    problem: str
    customer_wants: Literal["refund", "replacement", "information", "other"]
    mood: Literal["happy", "neutral", "annoyed", "angry"]


EXTRACT_SYSTEM = (
    "You extract facts from emails. Only use what is written. Use null if missing.\n"
    "order_id: only if an order number is actually written in the email, else null.\n"
    "mood, judged by the TONE, not by the problem itself:\n"
    "- angry: shouting (ALL CAPS, !!!), insults, or threats\n"
    "- annoyed: clearly complaining or frustrated, but not insulting\n"
    "- neutral: calm and polite, even if reporting a problem\n"
    "- happy: positive or thankful\n"
    "customer_wants: 'refund' if they ask for their money back in ANY wording.\n\n"
    "Examples:\n"
    "'parcel is late, can I get my money back? order C-111 - Jo' -> "
    "wants=refund, mood=neutral, order_id=C-111\n"
    "'still waiting on order C-222, this is really frustrating. please send a new one' -> "
    "wants=replacement, mood=annoyed, order_id=C-222\n"
    "'YOU PEOPLE ARE USELESS!!! WHERE IS MY ORDER' -> "
    "wants=information, mood=angry, order_id=null"
)


def extract_facts(email):
    raw = llm(
        f"Extract the facts from this customer email:\n\n{email}",
        system=EXTRACT_SYSTEM,
        schema=EmailFacts,
    )
    return EmailFacts.model_validate_json(raw)  # GATE: crashes here if the JSON is bad


# =====================================================================
# STEP 2: WRITE. Draft a reply from the clean facts, not the messy email.
# =====================================================================
def write_reply(facts):
    return llm(
        f"Customer facts:\n{facts.model_dump_json(indent=2)}\n\nCompany policy: {POLICY}\n\n"
        "Write a short, warm reply email to this customer. Apologise if they are upset, "
        "confirm what will happen next according to the policy, and reference their order ID. "
        "Sign it 'The Support Team'. Do not promise anything the policy doesn't say.",
        system="You are a friendly, professional customer support agent.",
    )


# =====================================================================
# THE WORKFLOW: step 1 -> (check) -> step 2
# =====================================================================
def handle_email(email):
    print("STEP 1: extracting facts...")
    try:
        facts = extract_facts(email)
    except ValidationError as e:
        print(f"   ❌ Step 1 produced invalid data, stopping:\n{e}")
        return None
    print(facts.model_dump_json(indent=2))  # we can SEE the middle of the pipeline

    print("\nSTEP 2: writing reply...")
    reply = write_reply(facts)
    print(reply)
    return reply


if __name__ == "__main__":
    print(f"Model: {MODEL}\n")
    print("=" * 70)
    print("CHAINED WORKFLOW (2 small, focused calls)")
    print("=" * 70)
    handle_email(EMAIL)

    print("\n" + "=" * 70)
    print("COMPARISON: ONE BIG PROMPT doing everything at once")
    print("=" * 70)
    print(llm(
        f"Customer email:\n{EMAIL}\n\nCompany policy: {POLICY}\n\n"
        "Write a short, warm reply. Reference their order ID. Sign it 'The Support Team'.",
        system="You are a friendly, professional customer support agent.",
    ))
