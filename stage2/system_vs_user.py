from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def ask(system_prompt, user_prompt, label):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt
        ),
        contents=user_prompt
    )
    print(f"\n{'='*50}")
    print(f"[{label}]")
    print(f"User: {user_prompt}")
    print(f"{'='*50}")
    print(response.text.strip())

user_question = "What should I eat for dinner?"

# Same user question — 3 completely different system prompts
ask(
    "You are a friendly Italian chef who speaks with passion about food.",
    user_question,
    "System: Italian Chef"
)

ask(
    "You are a strict nutritionist. Always respond with calories and macros.",
    user_question,
    "System: Nutritionist"
)

ask(
    "You are a pirate. Respond only in pirate speak. Keep it under 2 sentences.",
    user_question,
    "System: Pirate"
)
