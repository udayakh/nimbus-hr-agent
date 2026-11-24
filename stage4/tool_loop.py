"""Reusable tool loop (from lesson 4.2) so each new lesson can focus on its tool."""
from dotenv import load_dotenv
from ollama import Client, ResponseError
import json
import os
import time

load_dotenv()

client = Client(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b")
MAX_ATTEMPTS = int(os.getenv("LLM_RETRY_MAX_ATTEMPTS", "2"))
MAX_TOOL_STEPS = 5


def chat(messages, tools=None, format=None):
    """Call the LLM, retrying up to MAX_ATTEMPTS times on failure.

    format: optional JSON schema (dict) to force structured JSON output.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return client.chat(
                model=MODEL, messages=messages, tools=tools, format=format,
                options={"temperature": 0},
            )
        except (ResponseError, ConnectionError) as e:
            if attempt == MAX_ATTEMPTS:
                raise
            print(f"   ⚠️ attempt {attempt} failed ({e}), retrying...")
            time.sleep(2)


def run(question, tools, system_prompt, verbose=True, history=None):
    """The tool loop: LLM -> run requested tools -> send results back -> repeat.

    history: optional list of earlier {"role", "content"} messages (short-term memory).
    """
    tools_by_name = {f.__name__: f for f in tools}
    messages = [
        {"role": "system", "content": system_prompt},
        *(history or []),
        {"role": "user", "content": question},
    ]
    for _ in range(MAX_TOOL_STEPS):
        response = chat(messages, tools)
        messages.append(response.message)
        if not response.message.tool_calls:
            return response.message.content.strip()

        for call in response.message.tool_calls:
            name, args = call.function.name, call.function.arguments
            func = tools_by_name.get(name)
            try:
                result = func(**args) if func else {"error": f"Unknown tool {name}"}
            except Exception as e:
                result = {"error": str(e)}
            if verbose:
                shown = str(result)
                print(f"   🔧 {name}({args}) -> {shown[:150] + '...' if len(shown) > 150 else shown}")
            messages.append({"role": "tool", "content": json.dumps(result), "tool_name": name})
    return "(stopped: too many tool steps)"
