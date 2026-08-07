import os
from google import genai

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY_1")
)

response = client.models.generate_content(
    model="models/gemini-3.6-flash",
    contents="Who created you?"
)

print(response.text)