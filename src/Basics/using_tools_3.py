from google import genai
from google.genai import types
from dotenv import load_dotenv
import requests
import json
from pydantic import BaseModel , Field

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

response.function_calls

# Calling the function 
# When model calls a function , we must execute it and retun result. 
# Since model responses cam include zero , one or multiple calls , it is best practice to assume there are severals.

def call_function(name , args):

    if name == "get_weather":
        try:
            return get_weather(**args)
        except Exception as e: 
            return {"error" : str(e)}
    else:
        return {"error" : f"Tool with name : {name} is not available"}


messages.append(response.candidates[0].content)   # Gemini's own request, unchanged
messages
result_parts = []
for tool_call in response.function_calls:
    print(f"type of tool name : {type(tool_call.name)}")
    print(f"type of tool args : {type(tool_call.args)}")

    # arguments = json.loads(tool_call.args)
    print(f"type of json loads args : {type(tool_call.args)}")

    result = call_function(tool_call.name, tool_call.args)
    print(f"Function {tool_call.name} called with arguments {tool_call.args}. Result: {result}")
    result_parts.append(
        types.Part(
            function_response=types.FunctionResponse(
                id=tool_call.id,
                name=tool_call.name,
                response={"result": result},
            )
        )
    )


messages.append(types.Content(role="user", parts=result_parts))   # all results, one message


class WeatherResponse(BaseModel):

    temperature : float = Field(
        description = "The current temperature in celsius for the given location."
    )

    response : str = Field (
        description = "A natural language respone to the user's question"
    )



response = client.models.generate_content(
    model=MODEL,
    contents=messages,
    config=types.GenerateContentConfig(
        system_instruction="You are a helpful weather assistant.",
        tools=tools,
        response_mime_type = "application/json",
        response_schema = WeatherResponse
    ),
)

type(response)

event = response.parsed

event
type(event)