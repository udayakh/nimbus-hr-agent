from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Approach 1: Ask nicely (unreliable) ---
# The model might add markdown, extra text, or break the format.
print("=== APPROACH 1: Prompt-based JSON ===")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    ),
    contents='Extract the name, age, and city from this text as JSON:\n"Hi, I am Sara, 28 years old, living in Mumbai."'
)
print("Raw response:")
print(response.text)

# --- Approach 2: Force JSON (reliable) ---
# The API guarantees the response is always valid, parseable JSON.
print("\n=== APPROACH 2: Forced JSON (response_mime_type) ===")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    ),
    contents='Extract the name, age, and city from this text as JSON:\n"Hi, I am Sara, 28 years old, living in Mumbai."'
)
print("Raw response:")
print(response.text)

# Now parse it and use it like a normal Python dict
data = json.loads(response.text)
print("\nParsed as Python dict:")
print(f"  Name: {data['name']}")
print(f"  Age:  {data['age']}")
print(f"  City: {data['city']}")

# --- Real-world example: Extract multiple items ---
print("\n\n=== REAL EXAMPLE: Extract product list ===")
review = """
I bought three things last week: a blue running shoes for $85,
a water bottle for $12, and wireless earbuds for $45.
The shoes were great but the earbuds stopped working after 2 days.
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    ),
    contents=f'Extract all products from this review as a JSON array. Each item should have: name, price, satisfied (true/false).\n\nReview: {review}'
)

products = json.loads(response.text)
print(f"Found {len(products)} products:\n")
for p in products:
    status = "Happy" if p["satisfied"] else "Unhappy"
    print(f"  - {p['name']}: ${p['price']} -> {status}")
