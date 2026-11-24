from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Hello! Can you introduce yourself in 2 sentences?"
)

print("Gemini says:")
print(response.text)

print("\n--- Token Usage ---")
print(f"Input tokens:  {response.usage_metadata.prompt_token_count}")
print(f"Output tokens: {response.usage_metadata.candidates_token_count}")
print(f"Total tokens:  {response.usage_metadata.total_token_count}")

input_cost  = response.usage_metadata.prompt_token_count     / 1_000_000 * 0.15
output_cost = response.usage_metadata.candidates_token_count / 1_000_000 * 3.50
print(f"\nEstimated cost: ${input_cost + output_cost:.6f}")
