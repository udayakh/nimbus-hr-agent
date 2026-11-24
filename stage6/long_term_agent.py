"""Lesson 6.3: long-term memory. The agent remembers facts about you ACROSS sessions."""
import json
import sys
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from memory_agent import HRAgent, SYSTEM_PROMPT, MODEL
from tool_loop import chat as llm_chat

MEMORY_FILE = Path(__file__).parent / "long_term_memory.json"


# =====================================================================
# THE STORE: a plain JSON file on disk. It survives restarts.
# =====================================================================
class MemoryStore:
    def __init__(self, path=MEMORY_FILE):
        self.path = path

    def load(self):
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def add(self, fact):
        memories = self.load()
        if any(m["fact"].lower() == fact.lower() for m in memories):
            return False  # already known
        memories.append({"fact": fact, "saved": str(date.today())})
        self.path.write_text(json.dumps(memories, indent=2), encoding="utf-8")
        return True

    def clear(self):
        self.path.unlink(missing_ok=True)


# =====================================================================
# SAVING: after every message, a separate LLM step looks for lasting facts.
# This is a fixed workflow step (Stage 5 style), not a tool the agent must
# remember to call, which is more reliable for a small model.
# No names in the examples: the 3B model copies example names (lesson 6.2)!
# =====================================================================
class ExtractedFacts(BaseModel):
    facts: list[str]


EXTRACT_PROMPT = """Does the user's message state a LASTING fact about THEMSELVES?
Lasting facts: their name, job, team, or how they like to be answered.
NOT lasting facts: questions, one-off requests, facts about other people.

Write each fact as a short sentence starting with "The user".
If there are none, return an empty list.

Examples:
"I work night shifts, so mornings are hard for me" -> ["The user works night shifts"]
"From now on, please reply in bullet points" -> ["The user prefers answers in bullet points"]
"What's the weather like?" -> []
"Can you book a meeting for tomorrow?" -> []

User message: {message}"""


def extract_lasting_facts(message):
    response = llm_chat(
        [{"role": "user", "content": EXTRACT_PROMPT.format(message=message)}],
        format=ExtractedFacts.model_json_schema(),
    )
    return ExtractedFacts.model_validate_json(response.message.content).facts


# =====================================================================
# THE AGENT: the 6.2 agent + memories loaded into its system prompt
# =====================================================================
class LongTermAgent(HRAgent):
    def __init__(self, store=None, **kwargs):
        super().__init__(**kwargs)
        self.store = store or MemoryStore()

    def system_prompt(self):
        memories = self.store.load()
        if not memories:
            return SYSTEM_PROMPT
        known = "\n".join(f"- {m['fact']}" for m in memories)
        return (f"{SYSTEM_PROMPT}\n\nWhat you remember about the user from earlier sessions:\n"
                f"{known}\nWhen the user says 'I', 'me' or 'my', use these facts. "
                "Follow any answer-style preferences listed. If the user asks what you "
                "know or remember about them, list these facts (no tool needed).")

    def ask(self, question):
        answer = super().ask(question)
        for fact in extract_lasting_facts(question):
            if self.store.add(fact):
                print(f"   💾 remembered: {fact}")
        return answer


def chat():
    agent = LongTermAgent(mode="history")
    known = agent.store.load()
    print(f"Nimbus HR agent ({MODEL}) with long-term memory ({len(known)} facts loaded).")
    print("Commands: 'remember <fact>' saves a fact, 'memories' shows them, "
          "'forget' deletes them, 'quit' exits.\n")
    while True:
        q = input("You: ").replace("﻿", "").strip()  # ﻿: invisible char some terminals add
        if q.lower() in ("quit", "exit"):
            break
        if q.lower().startswith("remember "):
            # The RELIABLE path: the user says exactly what to save. No LLM involved.
            fact = q[len("remember "):].strip()
            print("   💾 saved\n" if agent.store.add(fact) else "   (already known)\n")
            continue
        if q.lower() == "memories":
            print(*(f"  - {m['fact']}" for m in agent.store.load()) or ["  (none)"], sep="\n")
            continue
        if q.lower() == "forget":
            agent.store.clear()
            print("(all long-term memories deleted)\n")
            continue
        if q:
            print(f"Agent: {agent.ask(q)}\n")


if __name__ == "__main__":
    if "--chat" in sys.argv:
        chat()
        sys.exit()

    store = MemoryStore()
    store.clear()  # start the demo with an empty memory file

    print("#" * 70 + "\n# SESSION 1 (Monday)\n" + "#" * 70)
    agent = LongTermAgent(store, mode="history")
    for q in ["Hi! I'm Aisha Khan and I work on the design team.",
              "Please always keep your answers to one sentence.",
              "What is the yearly learning budget?"]:
        print(f"\nYou:   {q}")
        print(f"Agent: {agent.ask(q)}")

    print("\n📁 long_term_memory.json now contains:")
    print(MEMORY_FILE.read_text(encoding="utf-8") if MEMORY_FILE.exists() else "(nothing)")

    print("#" * 70 + "\n# SESSION 2 (Tuesday): a brand-new agent, short-term memory empty\n" + "#" * 70)
    agent = LongTermAgent(store, mode="history")
    for q in ["How many vacation days do I have left?",
              "What do you know about me?"]:
        print(f"\nYou:   {q}")
        print(f"Agent: {agent.ask(q)}")
