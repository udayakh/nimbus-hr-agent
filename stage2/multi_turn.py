from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Demo 1: No memory (stateless calls) ---
# Each call is independent — the model forgets everything.
print("=== WITHOUT HISTORY (stateless) ===")

client.models.generate_content(
    model="gemini-2.5-flash",
    contents="My name is Uday."
)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is my name?"
)
print("Bot:", response.text.strip())
print("^ Model has no idea — each call is isolated.\n")

# --- Demo 2: With chat session (stateful) ---
# The chat object automatically tracks and sends full history each turn.
print("=== WITH CHAT SESSION (stateful) ===")

chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a helpful assistant. Be concise — answer in 1-2 sentences max.",
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )
)

turns = [
    "Hi! My name is Uday and I'm learning to build AI agents.",
    "What is my name and what am I learning?",
    "Give me one tip for someone at my stage.",
]

for user_msg in turns:
    print(f"You: {user_msg}")
    response = chat.send_message(user_msg)
    print(f"Bot: {response.text.strip()}\n")

# Show the full history the model sees
print("=== FULL HISTORY SENT ON LAST CALL ===")
for msg in chat.get_history():
    role = "You" if msg.role == "user" else "Bot"
    print(f"[{role}]: {msg.parts[0].text.strip()[:80]}...")
