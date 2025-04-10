import json
import sys # Import sys to exit if client fails
from prompt_utils import (
    get_openai_client,
    call_llm,
    default_system_prompt,
    default_user_prompt,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS
)

# --- Helper Functions (Input Handling) ---
# specific to the CLI
def get_multiline_input(prompt_message):
    """Gets multi-line input from the user."""
    print(f"{prompt_message} (Type 'EOF' on a new line when done):")
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "EOF":
                break
            lines.append(line)
        except EOFError: # Handles Ctrl+D in some terminals
            break
    return "\n".join(lines)

def get_float_input(prompt_message, default_value):
    """Gets float input with a default value."""
    while True:
        try:
            value_str = input(f"{prompt_message} (default: {default_value}): ")
            if not value_str:
                return default_value
            return float(value_str)
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_int_input(prompt_message, default_value):
    """Gets integer input with a default value."""
    while True:
        try:
            value_str = input(f"{prompt_message} (default: {default_value}): ")
            if not value_str:
                return default_value
            value = int(value_str)
            if value <= 0:
                print("Please enter a positive integer.")
            else:
                return value
        except ValueError:
            print("Invalid input. Please enter an integer.")


# --- Main Application Logic ---
def main():
    print("--- Prompt Wrangler CLI ---")

    client = get_openai_client()
    if not client:
        print("Exiting due to OpenAI client initialization failure.")
        sys.exit(1) # Exit if client setup failed

    # Use defaults from prompt_utils
    current_default_system_prompt = default_system_prompt
    current_default_user_prompt = default_user_prompt

    while True:
        print("\n--- New Run ---")

        # 1. Get Inputs
        system_prompt = input(f"Enter System Prompt (press Enter for default): ") or current_default_system_prompt
        user_prompt = input(f"Enter User Prompt (press Enter for default): ") or current_default_user_prompt
        input_text = get_multiline_input("Paste Input Text")
        temperature = get_float_input("Enter Temperature", default_value=DEFAULT_TEMPERATURE)
        max_tokens = get_int_input("Enter Max Tokens", default_value=DEFAULT_MAX_TOKENS)
        model_choice = input(f"Enter Model Name (default: {DEFAULT_MODEL}): ") or DEFAULT_MODEL

        if not input_text.strip():
            print("Input text cannot be empty. Please try again.")
            continue

        print(f"\nSending to {model_choice}...")

        # 2. Call LLM (using the imported function)
        output, p_tokens, c_tokens, t_tokens, r_time, error = call_llm(
            client,
            system_prompt,
            user_prompt,
            input_text,
            temperature,
            max_tokens,
            model_choice
        )

        # 3. Display Results
        print("\n--- Results ---")
        print(f"Response Time: {r_time:.2f} seconds")

        if error:
            print(f"API Call Failed: {error}")
        elif output:
            print(f"Token Usage: Prompt={p_tokens}, Completion={c_tokens}, Total={t_tokens}")
            print("\nStructured Output:")
            try:
                # Attempt to parse and pretty-print as JSON
                parsed_json = json.loads(output)
                print(json.dumps(parsed_json, indent=2))
            except json.JSONDecodeError:
                # If it's not valid JSON, print the raw output
                print("--------------------")
                print("(Output was not valid JSON, showing raw response)")
                print(output)
                print("--------------------")
        else:
            print("No output received.")

        # 4. Run Again?
        run_again = input("\nRun again? (y/n, default y): ").lower()
        if run_again == 'n':
            break

    print("\nExiting Prompt Wrangler CLI.")

if __name__ == "__main__":
    main()