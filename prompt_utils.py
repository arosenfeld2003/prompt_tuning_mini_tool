import os
import time
import json
from openai import OpenAI, APIError, RateLimitError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-4o-mini"
TEST_MODEL = "gpt-4o-mini" # Model to use for tests (can be different)
DEFAULT_TEMPERATURE = 0.3 # Lower temperature for more deterministic test results
DEFAULT_MAX_TOKENS = 250

# Default Prompts
default_system_prompt = (
    "You are an AI assistant specialized in extracting structured information from clinical notes. "
    "Your goal is to output the requested information strictly as a JSON object. "
    "Do not include any explanations, apologies, or introductory text outside the JSON structure. "
    "Only include fields that are explicitly mentioned or clearly implied in the input text."
)
default_user_prompt = (
    "Analyze the following clinical note and extract the key information into a JSON object. "
    "Use the following guidelines for categorization:\n"
    "- 'device': The main equipment (e.g., CPAP, wheelchair). Use 'product' if the request is for 'supplies'.\n"
    "- 'mask_type': Specific style for respiratory masks (e.g., full face).\n"
    "- 'type': General characteristic (e.g., lightweight, portable).\n"
    "- 'features': Integrated parts/capabilities (e.g., elevating leg rests, trazepe bar).\n"
    "- 'add_ons': Optional enhancements (e.g., humidifier).\n"
    "- 'accessories': External items needed for use (e.g., mouthpiece, tubing).\n"
    "- 'components': Individual items listed for a 'product' like supplies (e.g., filters, headgear).\n"
    "Also identify fields like 'diagnosis', 'qualifier', 'SpO2', 'usage', 'mobility_status', 'compliance_status', 'ordering_provider', etc., as applicable. "
    "Use lists for multiple items (like features, add_ons, accessories, components, usage).\n"
    "**Important:** Avoid using descriptive adjectives or qualifiers in the extracted values (e.g., use 'exertion' not 'during exertion', 'sleep' not 'during sleep'). Extract only the core noun or concept."
)

# --- OpenAI Client Initialization ---
def get_openai_client():
    """Initializes and returns the OpenAI client, handling potential errors."""
    if not API_KEY:
        print("ERROR: OPENAI_API_KEY not found in environment variables or .env file.")
        return None
    try:
        client = OpenAI(api_key=API_KEY)
        # Optional: Test connectivity with a simple request
        # client.models.list()
        return client
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return None

# --- Core LLM Call Function ---
def call_llm(client, system_prompt, user_prompt, input_text, temp, max_tok, model):
    """Makes the API call to OpenAI and measures time/tokens."""
    if client is None:
        return None, 0, 0, 0, 0, "OpenAI client not initialized."

    full_user_content = f"{user_prompt}\n\nInput Text:\n{input_text}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_user_content},
    ]

    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temp,
            max_tokens=max_tok,
            response_format={"type": "json_object"}
        )
        end_time = time.time()

        output_content = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        response_time = end_time - start_time

        return output_content, prompt_tokens, completion_tokens, total_tokens, response_time, None

    except (APIError, RateLimitError) as e:
        end_time = time.time()
        error_message = f"API Error: {e}"
        print(f"\n--- ERROR --- \n{error_message}\n-------------")
        return None, 0, 0, 0, end_time - start_time, error_message
    except Exception as e:
        end_time = time.time()
        error_message = f"An unexpected error occurred: {e}"
        print(f"\n--- ERROR --- \n{error_message}\n-------------")
        return None, 0, 0, 0, end_time - start_time, error_message