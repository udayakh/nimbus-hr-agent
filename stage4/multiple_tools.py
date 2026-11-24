from dotenv import load_dotenv
from ollama import Client, ResponseError
import json
import os
import time

load_dotenv()

# Local LLM via Ollama: no API key, no rate limits, no cost.
client = Client(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b")
MAX_ATTEMPTS = int(os.getenv("LLM_RETRY_MAX_ATTEMPTS", "2"))
MAX_TOOL_STEPS = 5  # safety limit so the agent can't loop forever

FAKE_HR_DATABASE = {
    "E101": {"name": "Priya Shah", "vacation_days_left": 18},
    "E102": {"name": "Marco Rossi", "vacation_days_left": 7},
    "E103": {"name": "Aisha Khan", "vacation_days_left": 12},
}


# =====================================================================
# TOOLS: plain Python functions.
# The ollama client reads the NAME, TYPE HINTS and DOCSTRING
# to build the tool description the LLM sees.
# =====================================================================

# DESIGN CHOICE: small models (like llama3.2:3b) struggle to CHAIN tools
# (call find_employee_id, then pass its result into another tool).
# So each tool accepts a NAME or an ID and does the lookup internally.
# Every task now needs just ONE tool call. Fewer, simpler tools = more reliable.

def _find_employee(employee):
    """Helper (NOT a tool, the LLM never sees it): match an ID or a name."""
    employee = str(employee or "").strip()
    if employee.upper() in FAKE_HR_DATABASE:
        return employee.upper(), FAKE_HR_DATABASE[employee.upper()]
    for emp_id, record in FAKE_HR_DATABASE.items():
        if employee and employee.lower() in record["name"].lower():
            return emp_id, record
    return None, None


def check_vacation_balance(employee: str) -> dict:
    """Look up how many vacation days an employee has left this year.

    Args:
        employee: The employee's name (e.g. "Priya") or ID (e.g. "E101").
    """
    emp_id, record = _find_employee(employee)
    if record is None:
        return {"error": f"No employee found matching '{employee}'"}
    return {"employee": record["name"], "employee_id": emp_id,
            "vacation_days_left": record["vacation_days_left"]}


def request_time_off(employee: str, start_date: str, days: int) -> dict:
    """Book vacation days for an employee. This deducts the days from their balance.

    Args:
        employee: The employee's name (e.g. "Marco") or ID (e.g. "E102").
        start_date: First day off, in YYYY-MM-DD format.
        days: Number of working days to take off.
    """
    emp_id, record = _find_employee(employee)
    if record is None:
        return {"error": f"No employee found matching '{employee}'"}
    try:
        days = int(days)  # small models sometimes send "3" instead of 3
    except (TypeError, ValueError):
        return {"error": f"'days' must be a number, got {days!r}"}
    if days > record["vacation_days_left"]:
        return {"error": f"Not enough days: requested {days}, only {record['vacation_days_left']} left"}
    record["vacation_days_left"] -= days  # this tool CHANGES data, it's an action
    return {"status": "approved", "employee": record["name"], "start_date": start_date,
            "days": days, "remaining": record["vacation_days_left"]}


TOOLS = [check_vacation_balance, request_time_off]
TOOLS_BY_NAME = {f.__name__: f for f in TOOLS}

SYSTEM_PROMPT = (
    "You are an HR assistant. Use the tools to look up and update employee data. "
    "Never guess balances. Only call a tool when the user asks about a specific "
    "employee's balance or wants to book time off. For general questions, answer "
    "directly without any tool."
)


def chat_with_retry(messages):
    """Call the LLM, retrying up to MAX_ATTEMPTS times on failure."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return client.chat(
                model=MODEL, messages=messages, tools=TOOLS, options={"temperature": 0}
            )
        except (ResponseError, ConnectionError) as e:
            if attempt == MAX_ATTEMPTS:
                raise
            print(f"   ⚠️ attempt {attempt} failed ({e}), retrying...")
            time.sleep(2)


def ask(question):
    """THE TOOL LOOP. This is the heart of every agent:
        1. send messages to the LLM
        2. if it asks for tools -> run them, add results to messages, go to 1
        3. if it replies with text -> done
    """
    print(f"\nQ: {question}")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for _ in range(MAX_TOOL_STEPS):
        response = chat_with_retry(messages)
        messages.append(response.message)  # remember what the LLM said / asked

        if not response.message.tool_calls:  # plain text -> final answer
            print(f"A: {response.message.content.strip()}")
            return

        for call in response.message.tool_calls:
            name, args = call.function.name, call.function.arguments
            print(f"   🔧 {name}({args})")
            func = TOOLS_BY_NAME.get(name)
            try:
                result = func(**args) if func else {"error": f"Unknown tool {name}"}
            except Exception as e:  # bad arguments from the LLM shouldn't crash us
                result = {"error": str(e)}
            print(f"      -> {result}")
            messages.append({"role": "tool", "content": json.dumps(result), "tool_name": name})

    print("A: (stopped: too many tool steps)")


if __name__ == "__main__":
    print(f"Model: {MODEL}  |  retries: {MAX_ATTEMPTS}")

    print("\n=== 1. LOOKING UP DATA ===")
    ask("How many vacation days does Priya have left?")

    print("\n=== 2. TAKING AN ACTION ===")
    ask("Please book 3 days off for Marco starting 2026-12-22.")

    print("\n=== 3. HANDLING A TOOL ERROR ===")
    ask("Book 10 more days off for Marco starting 2027-01-05.")

    print("\n=== 4. NO TOOL NEEDED ===")
    ask("What's a good way to ask my manager for time off?")
