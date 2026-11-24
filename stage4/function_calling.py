from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"


# =====================================================================
# 1. A normal Python function: the "tool".
#    Pretend this queries the company's HR database.
# =====================================================================
FAKE_HR_DATABASE = {
    "E101": {"name": "Priya", "vacation_days_left": 18, "sick_days_used": 2},
    "E102": {"name": "Marco", "vacation_days_left": 7, "sick_days_used": 0},
}


def check_vacation_balance(employee_id):
    print(f"   [Python] check_vacation_balance('{employee_id}') is running...")
    record = FAKE_HR_DATABASE.get(employee_id)
    if record is None:
        return {"error": f"No employee found with id {employee_id}"}
    return record


# =====================================================================
# 2. DESCRIBE the tool to the LLM.
#    The LLM only sees this description, never the code itself.
#    A clear description is how the LLM knows WHEN to use the tool.
# =====================================================================
vacation_tool = types.FunctionDeclaration(
    name="check_vacation_balance",
    description="Look up an employee's remaining vacation days and sick days used this year.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "employee_id": types.Schema(
                type="STRING", description="The employee ID, e.g. 'E101'"
            ),
        },
        required=["employee_id"],
    ),
)

config_with_tools = types.GenerateContentConfig(
    tools=[types.Tool(function_declarations=[vacation_tool])],
    thinking_config=types.ThinkingConfig(thinking_budget=0),
)

question = "I'm employee E102. How many vacation days do I have left?"


# ---------------------------------------------------------------------
print("=== DEMO 1: WITHOUT TOOLS ===")
print(f"Q: {question}")
response = client.models.generate_content(
    model=MODEL,
    contents=question,
    config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0)),
)
print(f"A: {response.text.strip()}")
print("^ The LLM has no way to know your personal data.\n")


# ---------------------------------------------------------------------
print("=== DEMO 2: WITH TOOLS. What does the LLM send back? ===")
print(f"Q: {question}")
response = client.models.generate_content(model=MODEL, contents=question, config=config_with_tools)

call = response.function_calls[0]
print(f"LLM text answer: {response.text!r}")
print(f"LLM function call: name={call.name!r}, args={dict(call.args)}")
print("^ No text answer. Just a REQUEST to call our function, with the right argument")
print("  pulled out of the sentence. Nothing has actually run yet!\n")


# ---------------------------------------------------------------------
print("=== DEMO 3: THE FULL ROUND TRIP ===")
# Step A: our code runs the function the LLM asked for
result = check_vacation_balance(**call.args)
print(f"   [Python] returned: {result}")

# Step B: send the whole conversation back, including the function result
conversation = [
    types.Content(role="user", parts=[types.Part(text=question)]),
    response.candidates[0].content,  # the LLM's function call
    types.Content(
        role="user",
        parts=[types.Part.from_function_response(name=call.name, response={"result": result})],
    ),
]
final = client.models.generate_content(model=MODEL, contents=conversation, config=config_with_tools)
print(f"A: {final.text.strip()}\n")


# ---------------------------------------------------------------------
print("=== DEMO 4: THE LLM DECIDES WHEN A TOOL IS NEEDED ===")
q = "What does 'PTO' stand for?"
print(f"Q: {q}")
response = client.models.generate_content(model=MODEL, contents=q, config=config_with_tools)
print(f"Function calls: {response.function_calls}")
print(f"A: {response.text.strip()}")
print("^ Tool was available but not needed, so the LLM just answered.")
