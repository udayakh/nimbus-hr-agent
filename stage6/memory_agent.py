"""Lesson 6.2: the HR agent from 6.1, now with short-term (conversation) memory."""
import copy
import functools
import sys

from hr_agent import TOOLS, SYSTEM_PROMPT, MODEL, run
from multiple_tools import FAKE_HR_DATABASE, request_time_off
from tool_loop import chat as llm_chat


# =====================================================================
# HUMAN-IN-THE-LOOP: actions that CHANGE data need a human "yes" first.
# The wrapper keeps the original name, parameters and docstring, so the
# LLM sees exactly the same tool. Only the behaviour changes.
# =====================================================================
def ask_human(description):
    answer = input(f"   ❓ Agent wants to: {description}. Allow? (y/n) ")
    answer = answer.replace("﻿", "").strip().lower()  # ﻿: invisible char some terminals add
    print(f"      human said: {answer or '(nothing)'}")
    return answer in ("y", "yes")


def requires_confirmation(func):
    @functools.wraps(func)
    def wrapper(**kwargs):
        details = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
        if ask_human(f"{func.__name__}({details})"):
            return func(**kwargs)
        return {"error": "The user REJECTED this action. Do not retry. Ask the user "
                         "to say clearly who and what they meant."}
    return wrapper


SAFE_TOOLS = [requires_confirmation(t) if t is request_time_off else t for t in TOOLS]

REWRITE_PROMPT = """Rewrite the user's LATEST message as one complete, standalone question.
Replace pronouns (he, she, his, her, they, them) and short follow-ups like "And X?"
with the exact names and topics they refer to in the conversation.
A pronoun refers to the MOST RECENTLY mentioned person, not the first one.
Only use names that appear in the conversation below.
If it is already standalone, return it unchanged. Output ONLY the rewritten question.

Conversation so far:
{history}

Latest message: {question}"""


class HRAgent:
    """An agent that remembers the last few turns of the conversation.

    mode:
      "none"    - no memory: every question starts from scratch
      "history" - send the past turns along with the new question (like lesson 2.4)
      "rewrite" - use the past turns to REWRITE the question into a standalone one,
                  then run the tools on that clear question (better for small models)

    We remember only each question + final answer, not the tool calls or raw
    tool results (e.g. whole handbook excerpts). That keeps the context small.
    """

    def __init__(self, mode="rewrite", max_turns=4):
        self.mode = mode
        self.max_turns = max_turns  # sliding window: only the last N turns are used
        self.history = []

    def system_prompt(self):
        """Subclasses can extend this (lesson 6.3 adds long-term memories)."""
        return SYSTEM_PROMPT

    def _recent(self):
        return self.history[-self.max_turns * 2:]

    def _rewrite(self, question):
        if not self.history:
            return question
        transcript = "\n".join(f"{m['role']}: {m['content']}" for m in self._recent())
        prompt = REWRITE_PROMPT.format(history=transcript, question=question)
        rewritten = llm_chat([{"role": "user", "content": prompt}]).message.content.strip()
        print(f"   ✏️  rewritten: {rewritten!r}")
        return rewritten

    def ask(self, question):
        if self.mode == "history":
            answer = run(question, SAFE_TOOLS, self.system_prompt(), history=self._recent())
        elif self.mode == "rewrite":
            answer = run(self._rewrite(question), SAFE_TOOLS, self.system_prompt())
        else:
            answer = run(question, SAFE_TOOLS, self.system_prompt())
        self.history += [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
        return answer

    def reset(self):
        self.history = []


# Aisha is NOT used as an example in any tool docstring, so the model can't guess her.
CONVERSATION = [
    "How many vacation days does Priya have left?",
    "And Aisha?",                                   # needs memory: what about Aisha?
    "Book 3 of her days off starting 2027-01-04.",  # "her" = Aisha
    "How many does she have now?",                  # "she" = Aisha
]


def chat():
    agent = HRAgent()
    print(f"Nimbus HR agent ({MODEL}). Commands: 'reset' clears memory, 'quit' exits.\n")
    while True:
        q = input("You: ").strip()
        if q.lower() in ("quit", "exit"):
            break
        if q.lower() == "reset":
            agent.reset()
            print("(memory cleared)\n")
            continue
        if q:
            print(f"Agent: {agent.ask(q)}\n")


if __name__ == "__main__":
    if "--chat" in sys.argv:
        chat()
        sys.exit()

    # The fake HR database lives in memory, so a booking in one run would change
    # the numbers in the next. Save a copy and restore it before each run.
    original = copy.deepcopy(FAKE_HR_DATABASE)

    modes = [a for a in sys.argv[1:] if a in ("none", "history", "rewrite")]
    for mode in modes or ["none", "history", "rewrite"]:
        FAKE_HR_DATABASE.clear()
        FAKE_HR_DATABASE.update(copy.deepcopy(original))
        print("\n" + "#" * 70 + f"\n# MEMORY MODE: {mode}\n" + "#" * 70)
        agent = HRAgent(mode=mode)
        for q in CONVERSATION:
            print(f"\nYou:   {q}")
            print(f"Agent: {agent.ask(q)}")
        print(f"\n   📒 Database afterwards: " +
              ", ".join(f"{r['name'].split()[0]}={r['vacation_days_left']}"
                        for r in FAKE_HR_DATABASE.values()))
