from google import genai
from google.genai import types
from dotenv import load_dotenv
import requests

load_dotenv()
client = genai.Client()
MODEL = "gemini-3.6-flash"


def get_weather(latitude, longitude):
    """Returns current weather for the given coordinates."""
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["current"]


get_weather_declaration = {
    "name": "get_weather",
    "description": "Get current weather for provided coordinates in celsius.",
    "parameters": {
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"},
        },
        "required": ["latitude", "longitude"],
    },
}

tools = [types.Tool(function_declarations=[get_weather_declaration])]

messages = [
    {"role": "user", "parts": [{"text": "What's the weather like in Paris today?"}]},
]

response = client.models.generate_content(
    model=MODEL,
    contents=messages,
    config=types.GenerateContentConfig(
        system_instruction="You are a helpful weather assistant.",
        tools=tools,
    ),
)

response
response.function_calls

# Calling the function 
# When model calls a function , we must execute it and retun result. 
# Since model responses cam include zero , one or multiple calls , it is best practice to assume there are severals.

def call_function(name , args):
    if name == "get_weather":
        return get_weather(**args)



for tool_call in response.function_calls:
    result = call_function(tool_call.name, tool_call.args)
    print(f"Function {tool_call.name} called with arguments {tool_call.args}. Result: {result}")
    messages.append(
        {"role": "tool", "tool_call_id": tool_call.id, "parts": [{"text": {result}}]}
    )