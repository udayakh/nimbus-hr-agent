from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def ask(prompt, temperature):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            temperature=temperature,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
        contents=prompt
    )
    print(f"\n--- Temperature: {temperature} ---")
    print((response.text or "(no response)").strip())

# --- Demo 1: Factual question ---
# Facts don't change with temperature — the answer is always Paris.
print("=== FACTUAL QUESTION ===")
print("Q: What is the capital of France?")
for temp in [0.0, 1.0, 2.0]:
    ask("What is the capital of France? Answer in one word.", temp)

# --- Demo 2: Creative task ---
# This is where temperature really shows its effect.
print("\n\n=== CREATIVE TASK ===")
print("Q: Write a one-sentence product slogan for a coffee brand.")
for temp in [0.0, 1.0, 2.0]:
    ask("Write a one-sentence product slogan for a coffee brand.", temp)

# --- Demo 3: max_output_tokens ---
# Hard-caps the response length — useful to control costs and keep replies short.
print("\n\n=== MAX OUTPUT TOKENS ===")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        temperature=1.0,
        max_output_tokens=30,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    ),
    contents="Explain what a neural network is."
)
print("With max_output_tokens=30 (cuts off mid-response):")
print(response.text.strip())
print(f"Output tokens used: {response.usage_metadata.candidates_token_count}")
