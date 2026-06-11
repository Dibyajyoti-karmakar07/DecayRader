import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for m in ["gemini-2.5-flash", "gemini-3.1-flash"]:
    try:
        print(f"Testing {m}...")
        res = client.models.generate_content(model=m, contents="hello")
        print(f"Success {m}:", res.text)
    except Exception as e:
        print(f"Failed {m}:", e)
