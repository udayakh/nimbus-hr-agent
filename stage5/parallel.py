import time
from concurrent.futures import ThreadPoolExecutor

from chain import llm, MODEL

EMAIL = """Hello, I ordered the blue backpack (order A-48213) two weeks ago and it still
hasn't arrived. The tracking page hasn't changed in a week. It was a birthday
present for my son, so I'm quite disappointed. Could you please refund me? - Dana"""


# =====================================================================
# Three INDEPENDENT LLM tasks: none needs another's result,
# so in theory they can all run at the same time.
# =====================================================================
def summarise(email):
    return llm(f"Summarise this email in ONE short sentence:\n\n{email}")


def translate(email):
    return llm(f"Translate this email into Spanish. Output only the translation:\n\n{email}")


def suggest_tags(email):
    return llm(f"Give 3 short support-ticket tags for this email, comma-separated, nothing else:\n\n{email}")


# Two NON-LLM tasks that just WAIT on other systems (simulated with sleep)
def lookup_order(order_id):
    time.sleep(2)  # pretend: slow database query
    return {"order_id": order_id, "status": "in transit", "last_update": "7 days ago"}


def lookup_customer(name):
    time.sleep(2)  # pretend: slow CRM (customer database) API call
    return {"name": name, "orders_last_year": 6, "vip": True}


def timed(label, fn):
    start = time.perf_counter()
    result = fn()
    print(f"   ⏱️  {label}: {time.perf_counter() - start:.1f}s")
    return result


def run_sequential(tasks):
    return {name: fn() for name, fn in tasks.items()}


def run_parallel(tasks):
    # Start every task at once on its own thread, then wait for all of them (FAN-OUT -> FAN-IN)
    with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        futures = {name: pool.submit(fn) for name, fn in tasks.items()}
        return {name: f.result() for name, f in futures.items()}


if __name__ == "__main__":
    print(f"Model: {MODEL}")
    llm("Say OK.")  # warm-up: load the model into memory so it doesn't skew the first timing

    llm_tasks = {
        "summary": lambda: summarise(EMAIL),
        "spanish": lambda: translate(EMAIL),
        "tags": lambda: suggest_tags(EMAIL),
    }
    waiting_tasks = {
        "order": lambda: lookup_order("A-48213"),
        "customer": lambda: lookup_customer("Dana"),
    }

    print("\n=== TEST 1: three LLM calls ===")
    timed("one after another", lambda: run_sequential(llm_tasks))
    timed("in parallel       ", lambda: run_parallel(llm_tasks))

    print("\n=== TEST 2: two slow lookups (no LLM) ===")
    timed("one after another", lambda: run_sequential(waiting_tasks))
    timed("in parallel       ", lambda: run_parallel(waiting_tasks))

    print("\n=== TEST 3: the real workflow, everything at once, then combine ===")
    results = timed("all 5 in parallel", lambda: run_parallel({**llm_tasks, **waiting_tasks}))

    # FAN-IN: combine every result into one report for a human agent (no LLM needed)
    c, o = results["customer"], results["order"]
    print(f"""
┌─ TICKET {o['order_id']} {'⭐ VIP' if c['vip'] else ''}
│ Customer: {c['name']} ({c['orders_last_year']} orders last year)
│ Order:    {o['status']}, last update {o['last_update']}
│ Summary:  {results['summary']}
│ Tags:     {results['tags']}
│ Spanish:  {results['spanish'][:80]}...
└─""")
