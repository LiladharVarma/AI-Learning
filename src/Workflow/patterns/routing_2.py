from typing import Optional, Literal
from datetime import datetime          
import logging
import time                            

from dotenv import load_dotenv         
from google import genai               
from google.genai import errors        
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()                          
client = genai.Client()                
MODEL = "gemini-3.6-flash"             


class CalendarRequestType(BaseModel):
    """Router LLM call: Determine the type of calendar request"""

    request_type: Literal["new_event", "modify_event", "other"] = Field(
        description="Type of calendar request being made"
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")
    description: str = Field(            
        description="The request text with all details kept: dates, times, names, durations"
    )


class NewEventDetails(BaseModel):
    """Details for creating a new event"""

    name: str = Field(description="Name of the event")
    date: str = Field(description="Date and time of the event (ISO 8601)")
    duration_minutes: int = Field(description="Duration in minutes")
    participants: list[str] = Field(description="List of participants")


class Change(BaseModel):
    """Details for changing an existing event"""

    field: str = Field(description="Field to change")
    new_value: str = Field(description="New value for the field")


class ModifyEventDetails(BaseModel):
    """Details for modifying an existing event"""

    event_identifier: str = Field(description="Description to identify the existing event")
    changes: list[Change] = Field(description="List of changes to make")
    participants_to_add: list[str] = Field(description="New participants to add")
    participants_to_remove: list[str] = Field(description="Participants to remove")


class CalendarResponse(BaseModel):
    """Final response format"""

    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="User-friendly response message")
    calendar_link: Optional[str] = Field(default=None, description="Calendar link if applicable")  


# CHANGED: this helper replaces every client.beta.chat.completions.parse(...)
def ask_gemini(user_text, system_instruction, schema, max_attempts=3):
    """One Gemini call that returns an object of the given schema class."""
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=user_text,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                },
            )
            return response.parsed
        except errors.ServerError as e:
            if attempt == max_attempts:
                raise
            wait = 2 ** attempt
            logger.warning(f"Gemini busy (attempt {attempt}/{max_attempts}), retrying in {wait}s: {e.code}")
            time.sleep(wait)


def today_text():                       
    return datetime.now().strftime("%A, %B %d, %Y")


def route_calendar_request(user_input: str) -> CalendarRequestType:
    """Router LLM call to determine the type of calendar request"""
    logger.info("Routing calendar request")

    result = ask_gemini(                
        user_text=user_input,
        system_instruction="Determine if this is a request to create a new calendar event or modify an existing one.",
        schema=CalendarRequestType,
    )
    logger.info(f"Request routed as: {result.request_type} with confidence: {result.confidence_score}")
    return result


def handle_new_event(description: str) -> CalendarResponse:
    """Process a new event request"""
    logger.info("Processing new event request")

    details = ask_gemini(               
        user_text=description,
        system_instruction=f"Today is {today_text()}. Extract details for creating a new calendar event.",
        schema=NewEventDetails,
    )
    logger.info(f"New event: {details.model_dump_json(indent=2)}")

    return CalendarResponse(
        success=True,
        message=f"Created new event '{details.name}' for {details.date} with {', '.join(details.participants)}",
        calendar_link=f"calendar://new?event={details.name}",
    )


def handle_modify_event(description: str) -> CalendarResponse:
    """Process an event modification request"""
    logger.info("Processing event modification request")

    details = ask_gemini(               
        user_text=description,
        system_instruction=f"Today is {today_text()}. Extract details for modifying an existing calendar event.",
        schema=ModifyEventDetails,
    )
    logger.info(f"Modified event: {details.model_dump_json(indent=2)}")

    return CalendarResponse(
        success=True,
        message=f"Modified event '{details.event_identifier}' with the requested changes",
        calendar_link=f"calendar://modify?event={details.event_identifier}",
    )


def process_calendar_request(user_input: str) -> Optional[CalendarResponse]:
    """Main function implementing the routing workflow"""
    logger.info("Processing calendar request")

    route_result = route_calendar_request(user_input)

    if route_result.confidence_score < 0.7:
        logger.warning(f"Low confidence score: {route_result.confidence_score}")
        return None

    if route_result.request_type == "new_event":
        return handle_new_event(route_result.description)
    elif route_result.request_type == "modify_event":
        return handle_modify_event(route_result.description)
    else:
        logger.warning("Request type not supported")
        return None


if __name__ == "__main__":
    result = process_calendar_request("Let's schedule a team meeting next Tuesday at 2pm with Alice and Bob")
    if result:
        print(f"Response: {result.message}")

    result = process_calendar_request("Can you move the team meeting with Alice and Bob to Wednesday at 3pm instead?")
    if result:
        print(f"Response: {result.message}")

    result = process_calendar_request("What's the weather like today?")
    if not result:
        print("Request not recognized as a calendar operation")