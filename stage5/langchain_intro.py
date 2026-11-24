"""Lesson 5.4: the same things you built by hand in 5.1-5.3, rebuilt with LangChain."""
import os
import time

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from chain import EmailFacts, POLICY  # reuse your schema + policy from 5.1

load_dotenv()

# =====================================================================
# 1. THE MODEL. Replaces your Client(...) + chat() helper.
#    .with_retry() replaces your hand-written retry loop.
# =====================================================================
model = ChatOllama(
    model=os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    temperature=0,
)
MAX_ATTEMPTS = int(os.getenv("LLM_RETRY_MAX_ATTEMPTS", "2"))
llm = model.with_retry(stop_after_attempt=MAX_ATTEMPTS)
to_text = StrOutputParser()  # turns the model's message object into a plain string

EMAIL = """hi, ordered the blue backpack (order #A-48213) over two weeks ago and still
nothing. it was a birthday present for my son. i'd like my money back please. - Dana"""


# =====================================================================
# 2. PROMPT TEMPLATES + THE PIPE |
#    A "chain" is pieces joined with |. Data flows left to right:
#    {"email": ...} -> prompt -> model -> plain text
# =====================================================================
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("user", "Summarise this email in ONE short sentence:\n\n{email}"),
])
summarise = summary_prompt | llm | to_text


# =====================================================================
# 3. STRUCTURED OUTPUT. Replaces format=schema + model_validate_json.
# =====================================================================
extract_prompt = ChatPromptTemplate.from_messages([
    ("system", "You extract facts from emails. Only use what is written. Use null if missing."),
    ("user", "Extract the facts from this customer email:\n\n{email}"),
])
extract = extract_prompt | model.with_structured_output(EmailFacts).with_retry(
    stop_after_attempt=MAX_ATTEMPTS
)


# =====================================================================
# 4. CHAINING TWO STEPS (lesson 5.1). Step 1's output feeds step 2.
#    RunnableLambda wraps a normal Python function so it can sit in the pipe.
# =====================================================================
reply_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a friendly, professional customer support agent."),
    ("user", "Customer facts:\n{facts}\n\nCompany policy: {policy}\n\n"
             "Write a short, warm reply (under 80 words). Reference the order ID. "
             "Sign it 'The Support Team'. Do not promise anything the policy doesn't say."),
])
facts_to_reply_input = RunnableLambda(
    lambda facts: {"facts": facts.model_dump_json(indent=2), "policy": POLICY}
)
handle_email = extract | facts_to_reply_input | reply_prompt | llm | to_text


# =====================================================================
# 5. PARALLEL (lesson 5.3). Replaces ThreadPoolExecutor.
# =====================================================================
translate = ChatPromptTemplate.from_template(
    "Translate this email into Spanish. Output only the translation:\n\n{email}") | llm | to_text
tags = ChatPromptTemplate.from_template(
    "Give 3 short support-ticket tags for this email, comma-separated, nothing else:\n\n{email}"
) | llm | to_text

all_at_once = RunnableParallel(summary=summarise, spanish=translate, tags=tags)


# =====================================================================
# 6. TOOLS (Stage 4). @tool replaces passing functions to ollama.chat().
# =====================================================================
@tool
def check_vacation_balance(employee: str) -> dict:
    """Look up how many vacation days an employee has left this year.

    Args:
        employee: The employee's name, e.g. "Priya".
    """
    return {"employee": employee, "vacation_days_left": 18}


model_with_tools = model.bind_tools([check_vacation_balance])


if __name__ == "__main__":
    print("=== 1. SIMPLE CHAIN: prompt | model | parser ===")
    print(summarise.invoke({"email": EMAIL}))

    print("\n=== 2. STRUCTURED OUTPUT ===")
    facts = extract.invoke({"email": EMAIL})
    print(f"{type(facts).__name__}: {facts}")

    print("\n=== 3. TWO-STEP CHAIN: extract | reshape | write ===")
    print(handle_email.invoke({"email": EMAIL}))

    print("\n=== 4. PARALLEL ===")
    start = time.perf_counter()
    results = all_at_once.invoke({"email": EMAIL})
    print(f"(took {time.perf_counter() - start:.1f}s)")
    for name, value in results.items():
        print(f"  {name}: {value[:90]}")

    print("\n=== 5. TOOLS: what the model asks for ===")
    msg = model_with_tools.invoke("How many vacation days does Priya have left?")
    print(f"tool_calls: {msg.tool_calls}")
    print("^ Same as Stage 4: the model only REQUESTS the call. Running it is still up to you.")

    print("\n=== 6. BATCH: run one chain on many inputs ===")
    for s in summarise.batch([{"email": "My parcel arrived broken."},
                              {"email": "Thanks, the delivery was super fast!"}]):
        print(f"  - {s}")
