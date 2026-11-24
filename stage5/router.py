from datetime import date, timedelta

from pydantic import ValidationError

from chain import extract_facts, llm, MODEL

TODAY = date.today()

# Pretend order database
ORDERS = {
    "A-48213": {"item": "blue backpack", "ordered": TODAY - timedelta(days=16), "delivered": False},
    "B-10007": {"item": "water bottle", "ordered": TODAY - timedelta(days=3), "delivered": False},
}
REFUND_AFTER_DAYS = 10


def draft(instructions, facts):
    """Shared LLM call for writing a reply, given route-specific instructions."""
    return llm(
        f"Customer facts:\n{facts.model_dump_json(indent=2)}\n\n{instructions}\n"
        "Keep it under 100 words. Sign it 'The Support Team'. Only state facts given here.",
        system="You are a friendly, professional customer support agent.",
    )


# =====================================================================
# THE ROUTES: one function per path through the workflow
# =====================================================================

def route_missing_order_id(facts):
    # No LLM needed! A fixed template is cheaper, faster and 100% predictable.
    return (f"Hi {facts.customer_name},\n\nThanks for getting in touch. Could you send us your "
            "order number (it looks like A-12345)? Then we can look into this right away.\n\n"
            "The Support Team")


def route_escalate(facts):
    # Angry customers go to a human. The bot only sends a short holding reply.
    print(f"   🚨 Ticket created for a human agent: {facts.order_id} / {facts.problem}")
    return draft("The customer is upset. Apologise sincerely and say a senior team member "
                 "will personally contact them within 24 hours. Do not offer anything else.", facts)


def route_refund(facts):
    order = ORDERS.get(facts.order_id)
    if order is None:
        return draft("We could not find this order ID. Ask them to double-check it.", facts)

    # The BUSINESS RULE is decided in Python, never by the LLM.
    days_waiting = (TODAY - order["ordered"]).days
    print(f"   📦 {order['item']}: ordered {days_waiting} days ago, delivered={order['delivered']}")
    if not order["delivered"] and days_waiting >= REFUND_AFTER_DAYS:
        print("   ✅ Eligible for refund")
        return draft(f"APPROVED: a full refund for their {order['item']}, processed within "
                     "5 business days. Apologise for the delay.", facts)
    print("   ⏳ Not eligible yet")
    return draft(f"NOT eligible for a refund yet: the order was placed only {days_waiting} days "
                 f"ago and refunds apply after {REFUND_AFTER_DAYS} days. Explain kindly that it "
                 "is still on its way and they can contact us again if it hasn't arrived by then.",
                 facts)


def route_general(facts):
    return draft("Answer their request helpfully. If you don't have the information, "
                 "say a team member will follow up.", facts)


# =====================================================================
# A CODE CHECK to back up the LLM's "angry" label.
# Small models over-use "angry". For an important decision (pulling in a
# human), we also require a signal that plain Python can verify.
# =====================================================================
INSULT_WORDS = {"joke", "useless", "worst", "disgusted", "scam", "pathetic", "ridiculous"}


def shows_anger(email):
    words = [w.strip(".,!?-") for w in email.split()]
    shouted = sum(1 for w in words if len(w) > 2 and w.isupper())
    insults = any(w.lower() in INSULT_WORDS for w in words)
    return shouted >= 3 or "!!" in email or insults


# =====================================================================
# THE ROUTER: plain if/else, driven by what the LLM extracted
# =====================================================================
def handle_email(email):
    try:
        facts = extract_facts(email)  # Step 1 (LLM)
    except ValidationError:
        return "route: FAILED", "Could not understand the email. Sent to a human."

    angry_signal = shows_anger(email)
    print(f"   facts: wants={facts.customer_wants}, mood={facts.mood}, order_id={facts.order_id}"
          f"  |  code anger check: {angry_signal}")

    # Order matters: the most important checks come first
    if facts.mood == "angry" and angry_signal:  # LLM AND code must agree
        return "route: ESCALATE", route_escalate(facts)
    if not facts.order_id:
        return "route: ASK FOR ORDER ID", route_missing_order_id(facts)
    if facts.customer_wants == "refund":
        return "route: REFUND", route_refund(facts)
    return "route: GENERAL", route_general(facts)


TEST_EMAILS = {
    "Late order, wants refund": """hi, ordered the blue backpack (order #A-48213) over two weeks ago
and still nothing. i'd like my money back please. - Dana""",

    "Too early for refund": """Hello, I ordered a water bottle, order B-10007, a few days ago.
It hasn't come yet so I'd like a refund. Thanks, Sam""",

    "No order number": """Hey, my package never arrived and I want a refund. Can you help? Lee""",

    "Furious customer": """THIS IS THE THIRD TIME I'M WRITING!!! Order A-48213 is a JOKE.
Worst company ever, I am disgusted and will be telling everyone. - Chris""",
}


if __name__ == "__main__":
    print(f"Model: {MODEL}  |  Today: {TODAY}")
    for label, email in TEST_EMAILS.items():
        print("\n" + "=" * 70)
        print(f"📧 {label}")
        route, reply = handle_email(email)
        print(f"   ➡️  {route}\n")
        print(reply)
