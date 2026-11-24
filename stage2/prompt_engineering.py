from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def ask(prompt, label):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    print(f"\n{'='*50}")
    print(f"[{label}]")
    print(f"{'='*50}")
    print(response.text.strip())

# --- Technique 1: Zero-shot ---
# Just ask. No examples. No context.
ask(
    "Classify this review as positive or negative: 'The food was cold and the service was slow.'",
    "1. Zero-shot"
)

# --- Technique 2: Few-shot ---
# Show examples first so the model learns the format you want.
ask(
    """Classify each review as positive or negative.

Review: "Amazing service and great food!" → Positive
Review: "Never coming back, worst experience ever." → Negative
Review: "It was okay, nothing special." → Neutral

Review: "The food was cold and the service was slow." →""",
    "2. Few-shot (with examples)"
)

# --- Technique 3: Role prompting ---
# Give the model a persona to shape its tone and expertise.
ask(
    """You are a harsh food critic with 20 years of experience who never sugarcoats opinions.

Write a one-sentence verdict on this restaurant review:
'The food was cold and the service was slow.'""",
    "3. Role prompting"
)

# --- Technique 4: Be specific about format ---
ask(
    """Classify this review and explain why in exactly one sentence.
Format: LABEL | Reason

Review: 'The food was cold and the service was slow.'""",
    "4. Specific format"
)
