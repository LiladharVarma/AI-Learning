
from google import genai
import time
from google.genai import errors
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

MODEL = "gemini-3.6-flash"

messages = [
    {
            "role": "model",
            "parts": [{"text": "You're a helpful assistant."}],
    },
    {
        "role": "user",
        "parts": [{"text": "Write a limerick about the Python programming language."}],
    },
]

completion = client.models.generate_content(
    model=MODEL,
    contents= messages
)

print(completion.text)