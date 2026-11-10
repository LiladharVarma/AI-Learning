from dotenv import load_dotenv
from google import genai
import time
from google.genai import errors

load_dotenv()
client = genai.Client()

MODEL = "gemini-3.6-flash"

for attempt in range (3):
    try :
        response = client.models.generate_content(
            model=MODEL,
            contents="Say hello in five words",
        )
        print(response.text)
        break
    except errors.ServerError:
        print("Failed, waiting")
        time.sleep(1)


