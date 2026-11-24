"""Lesson 5.5: the 5.2 support router, rebuilt as one LangChain pipeline.

    email ─▶ [extract facts  ‖  code anger check]   (both at once)
          ─▶ branch: escalate / ask for order ID / refund / general
          ─▶ {"route": ..., "reply": ...}
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough

from chain import EXTRACT_SYSTEM, EmailFacts
from langchain_intro import llm, model, to_text, MAX_ATTEMPTS
from router import ORDERS, REFUND_AFTER_DAYS, TEST_EMAILS, TODAY, shows_anger

# =====================================================================
# STEP 1: EXTRACT (your improved prompt from 5.2, now as a LangChain chain)
# =====================================================================
extract = (
    ChatPromptTemplate.from_messages([
        ("system", EXTRACT_SYSTEM),
        ("user", "Extract the facts from this customer email:\n\n{email}"),
    ])
    | model.with_structured_output(EmailFacts).with_retry(stop_after_attempt=MAX_ATTEMPTS)
)

# =====================================================================
# SHARED REPLY WRITER: every LLM route uses this, with different instructions
# =====================================================================
draft = (
    RunnableLambda(lambda x: {"facts": x["facts"].model_dump_json(indent=2),
                              "instructions": x["instructions"]})
    | ChatPromptTemplate.from_messages([
        ("system", "You are a friendly, professional customer support agent."),
        ("user", "Customer facts:\n{facts}\n\n{instructions}\n"
                 "Keep it under 100 words. Sign it 'The Support Team'. Only state facts given here."),
    ])
    | llm
    | to_text
)


def llm_route(name, instructions_fn):
    """Build a route: work out instructions (Python) -> draft reply (LLM) -> label it."""
    return (
        RunnablePassthrough.assign(instructions=RunnableLambda(instructions_fn))
        | RunnablePassthrough.assign(reply=draft)
        | RunnableLambda(lambda x: {"route": name, "reply": x["reply"]})
    )


# =====================================================================
# THE ROUTES. Business rules stay in plain Python.
# =====================================================================
def escalate_instructions(x):
    print(f"   🚨 Ticket created for a human agent: {x['facts'].order_id}")
    return ("The customer is upset. Apologise sincerely and say a senior team member will "
            "personally contact them within 24 hours. Do not offer anything else.")


def refund_instructions(x):
    order = ORDERS.get(x["facts"].order_id)
    if order is None:
        return "We could not find this order ID. Ask them to double-check it."
    days = (TODAY - order["ordered"]).days
    if not order["delivered"] and days >= REFUND_AFTER_DAYS:
        print(f"   ✅ Refund eligible ({days} days)")
        return (f"APPROVED: a full refund for their {order['item']}, processed within "
                "5 business days. Apologise for the delay.")
    print(f"   ⏳ Not eligible yet ({days} days)")
    return (f"NOT eligible for a refund yet: ordered only {days} days ago and refunds apply after "
            f"{REFUND_AFTER_DAYS} days. Explain kindly it is still on its way and they can "
            "contact us again if it hasn't arrived by then.")


ask_for_order_id = RunnableLambda(lambda x: {  # no LLM: a fixed template
    "route": "ASK FOR ORDER ID",
    "reply": f"Hi {x['facts'].customer_name},\n\nThanks for getting in touch. Could you send us "
             "your order number (it looks like A-12345)? Then we can look into this right away."
             "\n\nThe Support Team",
})

# =====================================================================
# THE PIPELINE
# =====================================================================
pipeline = (
    # Adds "facts" and "angry_signal" next to "email". The two run IN PARALLEL.
    RunnablePassthrough.assign(
        facts=extract,
        angry_signal=RunnableLambda(lambda x: shows_anger(x["email"])),
    )
    # RunnableBranch = if / elif / elif / else. The first condition that is True wins.
    | RunnableBranch(
        (lambda x: x["facts"].mood == "angry" and x["angry_signal"],
         llm_route("ESCALATE", escalate_instructions)),
        (lambda x: not x["facts"].order_id, ask_for_order_id),
        (lambda x: x["facts"].customer_wants == "refund",
         llm_route("REFUND", refund_instructions)),
        llm_route("GENERAL", lambda x: "Answer their request helpfully. If you don't have the "
                                       "information, say a team member will follow up."),
    )
)


if __name__ == "__main__":
    print(f"Today: {TODAY}")
    for label, email in TEST_EMAILS.items():
        print("\n" + "=" * 70)
        print(f"📧 {label}")
        result = pipeline.invoke({"email": email})
        print(f"   ➡️  route: {result['route']}\n")
        print(result["reply"])
