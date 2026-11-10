# import os
from google import genai

from google.genai import errors , types
from dotenv import load_dotenv
from pydantic import BaseModel, Field 

load_dotenv()
client = genai.Client()
MODEL = "gemini-3.6-flash"


# Response format for structured output
class CalenderEvent(BaseModel):

    name:str
    date:str
    participants:list[str]

# messages to send to the model

messages = [
    {
        "role": "model",
        "parts": [{"text": "Extract the event information."}],
    },
    {
        "role": "user", 
        "parts": [{"text": "Alice and Bob are going to a science fair on Friday."}],

    }
]



# Call the model 

response = client.models.generate_content(
    model = MODEL ,
    contents = messages,
    config = types.GenerateContentConfig(
        response_mime_type = "application/json",
        response_schema = CalenderEvent
    )

)

# print(f"This is the completuion object : {completion}")
event = response.parsed
if event is None:
    print("No structured result")
else:
    print(event)
    print(event.name, "|", event.date, "|", event.participants)
    print(type(event))
# print(f"This is the completion text : {completion.text}")
