from datetime import datetime
from pydantic import BaseModel , Field 
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging
from typing import Optional

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()
client = genai.Client()
MODEL = "gemini-3.6-flash"


class EventExtraction(BaseModel):

    """First LLM call: Extract basic event information"""

    description : str = Field(description="Description of the event to extract information from.")
    is_calendar_event :bool  = Field(description="Whether the event is a calendar event or not.")
    confidence : float = Field(description="Confidence score of the event extraction between 0 and 1.")

class EventDetails(BaseModel):
    """Second LLM call: Parse specific event details"""

    name: str = Field(description="Name of the event")
    date: str = Field(
        description="Date and time of the event. Use ISO 8601 to format this value."
    )
    duration_minutes: int = Field(description="Expected duration in minutes")
    participants: list[str] = Field(description="List of participants")


class EventConfirmation(BaseModel):
    """Third LLM call: Generate confirmation message"""

    confirmation_message: str = Field(
        description="Natural language confirmation message"
    )
    calendar_link: Optional[str] = Field(
        description="Generated calendar link if applicable"
    )

# resusable function to call Gemini API with given model , messages , system instructions and response schema.
def ask_gemini(model :str , messages : list[dict] , sys_instructions : str  , response_schema : BaseModel):
     response = client.models.generate_content(
        model=MODEL,
        contents = messages,
        config={
            "system_instruction": sys_instructions,
            "response_mime_type": "application/json",
            "response_schema": response_schema
        },
    )

     return response.parsed



def extract_event_info(user_input : str) -> EventExtraction :
    """First LLM call to determine if input is a calendar event"""

    logger.info("Starting event extraction analysis")
    logger.debug(f"Input text: {user_input}")

    today = datetime.now().strftime("%A, %B %d, %Y")

    event = ask_gemini(
        model = MODEL,
        sys_instructions = f"You are a helpful assistant that extracts event information from a given description. Today's date is {today}.",
        messages = [
            {"role": "user", "parts":[{"text" : user_input }]}
        ],
        response_schema = EventExtraction
    )

    logger.info(
        f"Extraction complete - Is calendar event: {event.is_calendar_event}, Confidence: {event.confidence:.2f}"
    )

    return event


def parse_event_details(description):
    today = datetime.now().strftime("%A, %B %d, %Y")

    response = ask_gemini(
        model = MODEL ,
        messages = [
            {"role": "user", "parts":[{"text" : description }]}
        ],
        sys_instructions= f"You are a helpful assistant that parse event information from a given description. Today's date is {today}.",
        response_schema=EventDetails
    )

    return response


def generate_confirmation(event_details: EventDetails) -> EventConfirmation:
    """Third LLM call to generate a confirmation message"""
    logger.info("Generating confirmation message")
    
    result = ask_gemini(
            model = MODEL , 
            messages = [
               
                {"role": "user", "parts": [{"text": event_details}]},
            ],
            sys_instructions=f"Generate a natural confirmation message for the event. Sign of with your name; Susie",
            response_schema=EventConfirmation
        )
    
    logger.info("Confirmation message generated successfully")
    return result



def process_calendar_request(user_input)-> Optional[ EventConfirmation]:
    """Main function implementing the prompt chain with gate check"""
    logger.info("Processing calendar request")
    logger.debug(f"Raw input: {user_input}")

    # First LLM call to extact the event 
    first = extract_event_info(user_input)


    # Gate check to make sure if its not calender event there is no need to call LLM 
    if not first.is_calendar_event or first.confidence < 0.7:
        print("Gate failed: is_calendar_event =", first.is_calendar_event, "| confidence =", first.confidence)
        return None

    logger.info("Gate check passed, proceeding with event processing")


     # Second LLM call: Get detailed event information
    details = parse_event_details(first.description)
    logger.info(f"Event details parsed: {details}")
    # Third LLM call for confirmation message generation 
    confirmation = generate_confirmation(details)

    return confirmation



# first is valid input and second is invalid input 
for text in [
    "Let's schedule a 1h team meeting next Tuesday at 2pm with Alice and Bob to discuss the project roadmap.",
    "Can you send an email to Alice and Bob to discuss the project roadmap?",
]:
    result = process_calendar_request(text)
    if result:
        print(result)
    else:
        print("This doesn't appear to be a calendar event request.")


text = "Let's schedule a 1h team meeting next Tuesday at 2pm with Alice and Bob to discuss the project roadmap."

result = process_calendar_request(text)
if result:
    print(result)
else:
    print("This doesn't appear to be a calendar event request.")