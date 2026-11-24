from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a helpful assistant named Aria. Be friendly and concise.",
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )
)

print("Aria is ready! Type 'quit' to exit.\n")

while True:
    user_input = input("You: ").strip()
    if not user_input:
        continue
    if user_input.lower() in ("quit", "exit", "bye"):
        print("Aria: Goodbye! Great chatting with you.")
        break

    response = chat.send_message(user_input)
    print(f"Aria: {response.text.strip()}\n")
