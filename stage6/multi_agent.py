"""Lesson 6.4: a multi-agent system. A supervisor plans, specialists do the work."""
import functools
from typing import Literal

from pydantic import BaseModel

from hr_agent import search_handbook, check_vacation_balance, MODEL
from memory_agent import SAFE_TOOLS  # HR tools, with human confirmation on bookings
from tool_loop import chat, run
from calculator import calculate
from web_search import web_search
from file_tools import list_files, read_file, write_file


# =====================================================================
# THE SPECIALISTS: each has a FEW tools and a FOCUSED system prompt.
# =====================================================================
SPECIALISTS = {
    "hr": {
        "description": "company HR policy (vacation, leave, budgets, expenses), employees' "
                       "vacation balances, AND booking time off. It has direct access to the "
                       "employee database, so one hr step is enough for any HR request",
        "tools": SAFE_TOOLS,
        "prompt": "You are the HR specialist. Use search_handbook for policies, "
                  "check_vacation_balance for balances, request_time_off only to book. "
                  "Answer only from tool results, in 1-2 sentences.",
    },
    "research": {
        "description": "current information from the internet (latest versions, news, recent facts)",
        "tools": [web_search],
        "prompt": "You are the research specialist. Always call web_search, then answer "
                  "in 1-2 sentences using only the results. Include the source URL.",
    },
    "files": {
        "description": "ONLY when the user explicitly asks to list, read or save a file "
                       "(e.g. 'save this to notes.txt'). It has NO employee or HR data",
        "tools": [list_files, read_file, write_file],
        "prompt": "You are the files specialist. Use the file tools to do exactly what "
                  "the task says, then say briefly what you did.",
    },
    "math": {
        "description": "any calculation or arithmetic",
        "tools": [calculate],
        "prompt": "You are the math specialist. Always use the calculate tool, copying "
                  "numbers exactly (keep decimal points). State the result clearly.",
    },
}


# =====================================================================
# THE SUPERVISOR: turns a request into a PLAN of steps.
# It never calls tools itself, it only decides WHO does WHAT.
# =====================================================================
class Step(BaseModel):
    agent: Literal["hr", "research", "files", "math"]
    task: str


class Plan(BaseModel):
    steps: list[Step]


team = "\n".join(f"- {name}: {s['description']}" for name, s in SPECIALISTS.items())
SUPERVISOR_PROMPT = f"""You are a supervisor. Split the user's request into steps and
assign each step to ONE specialist:
{team}

Rules:
- Use as FEW steps as possible. Most requests need exactly 1 step.
- Only add a second step if the request clearly asks for two different things
  (for example: find something AND save it).
- Each task must be a complete instruction the specialist can do alone.
- Copy names, numbers and filenames from the request exactly.

User request: {{request}}"""


def make_plan(request):
    response = chat([{"role": "user", "content": SUPERVISOR_PROMPT.format(request=request)}],
                    format=Plan.model_json_schema())
    return Plan.model_validate_json(response.message.content)


def watch(tools, log):
    """Wrap tools so the SUPERVISOR (code) sees every tool result, not just the
    agent's final text. Agents can hide a failure behind confident words."""
    def wrap(func):
        @functools.wraps(func)
        def wrapper(**kwargs):
            result = func(**kwargs)
            log.append(result)
            return result
        return wrapper
    return [wrap(t) for t in tools]


def step_failed(log):
    """A step failed if it used no tool at all, or its LAST tool call returned an error."""
    return not log or (isinstance(log[-1], dict) and "error" in log[-1])


def handle(request):
    plan = make_plan(request)
    print("   🧭 plan: " + " → ".join(f"[{s.agent}] {s.task}" for s in plan.steps))

    previous = None
    for i, step in enumerate(plan.steps[:3]):  # safety limit on plan length
        specialist = SPECIALISTS[step.agent]
        task = step.task
        if previous:  # HAND-OFF: pass the last specialist's result to the next one
            task += f"\n\nResult from the previous step (use this): {previous}"
        print(f"   ▶️  {step.agent} agent working...")
        log = []
        previous = run(task, watch(specialist["tools"], log), specialist["prompt"])

        # QUALITY GATE: don't hand a failed result to the next agent
        is_last = i == len(plan.steps[:3]) - 1
        if not is_last and step_failed(log):
            reason = log[-1]["error"] if log else "no tool was used"
            print(f"   🛑 {step.agent} step failed ({reason}). Stopping the plan.")
            return (f"Sorry, I couldn't finish this: the {step.agent} step failed "
                    f"({reason}). Nothing was saved. Please try again.")
    return previous


REQUESTS = [
    "How many vacation days does Aisha have left?",
    "What is 15% of 2,340?",
    "What is the latest version of Python?",
    "What files are in my workspace?",
    "Find the latest Python version online and save it to a file called python_version.txt",
]


if __name__ == "__main__":
    print(f"Model: {MODEL}  |  Specialists: {', '.join(SPECIALISTS)}")
    for r in REQUESTS:
        print("\n" + "=" * 70)
        print(f"👤 {r}")
        print(f"🤖 {handle(r)}")
