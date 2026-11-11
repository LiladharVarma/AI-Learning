from datetime import datetime
from pydantic import BaseModel , Field 
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging

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
    is_calendeer_event :bool  = Field(description="Whether the event is a calendar event or not.")
    confidence : float = Field(description="Confidence score of the event extraction between 0 and 1.")


# resusable function to call Gemini API with given model , messages , system instructions and response schema.
def ask_gemini(model :str , messages : list[dict] , sys_instructions : str  , response_schema : BaseModel):
     response = client.models.generate_content(
        model=MODEL,
        contents = messages,
        config={
            "system_instruction": sys_instructions,
            ,
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
            {"role": "user", "content": user_input}
        ],
        response_schema = EventExtraction
    )

    logger.info(
        f"Extraction complete - Is calendar event: {event.is_calendar_event}, Confidence: {event.confidence:.2f}"
    )

    return event

print(extract_event_info("Let's schedule a 1h team meeting next Tuesday at 2pm with Alice and Bob."))
# print(extract_event_info("Can you send an email to Alice and Bob?"))