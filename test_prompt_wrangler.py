import json
import sys
import os
from datetime import datetime
from pathlib import Path # Use pathlib for easier path manipulation
from deepdiff import DeepDiff
from prompt_utils import (
    get_openai_client,
    call_llm,
    default_system_prompt,
    default_user_prompt,
    TEST_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS
)

# Define test cases
TEST_CASES = [
    {
        "input": "Patient requires a full face CPAP mask with humidifier due to AHI > 20. Ordered by Dr. Cameron.",
        "expected_output": {
            "device": "CPAP",
            "mask_type": "full face",
            "add_ons": ["humidifier"],
            "qualifier": "AHI > 20",
            "ordering_provider": "Dr. Cameron"
        }
    },
    {
        "input": "Patient diagnosed with COPD, SpO2 measured at 87% on room air. Needs portable oxygen concentrator for use during exertion and sleep. Dr. Chase signed the order.",
        "expected_output": {
            "device": "portable oxygen concentrator",
            "diagnosis": "COPD",
            "SpO2": "87%",
            "usage": ["exertion", "sleep"],
            "ordering_provider": "Dr. Chase"
        }
    },
    {
        "input": "Patient has MS with significant mobility issues. Recommended a lightweight manual wheelchair with elevating leg rests. Ordered by Dr. Taub.",
        "expected_output": {
            "device": "manual wheelchair",
            "type": "lightweight",
            "features": ["elevating leg rests"],
            "diagnosis": "MS",
            "ordering_provider": "Dr. Taub"
        }
    },
    {
        "input": "Asthma diagnosis confirmed. Prescribing nebulizer with mouthpiece and tubing. Dr. Foreman completed the documentation.",
        "expected_output": {
            "device": "nebulizer",
            "accessories": ["mouthpiece", "tubing"],
            "diagnosis": "Asthma",
            "ordering_provider": "Dr. Foreman"
        }
    },
    {
        "input": "Patient is non-ambulatory and requires hospital bed with trapeze bar and side rails. Diagnosis: late-stage ALS. Order submitted by Dr. Cuddy.",
        "expected_output": {
            "device": "hospital bed",
            "features": ["trapeze bar", "side rails"],
            "diagnosis": "ALS",
            "mobility_status": "non-ambulatory",
            "ordering_provider": "Dr. Cuddy"
        }
    },
    {
        "input": "CPAP supplies requested. Full face mask with headgear and filters. Patient has been compliant. Ordered by Dr. House.",
        "expected_output": {
            "product": "CPAP supplies",
            "components": ["full face mask", "headgear", "filters"],
            "compliance_status": "compliant",
            "ordering_provider": "Dr. House"
        }
    }
]

def format_diff(diff):
    """Formats the DeepDiff object into more readable messages."""
    messages = []
    # Dictionary changes
    if 'dictionary_item_added' in diff:
        for item in diff['dictionary_item_added']:
            messages.append(f"- Key Missing in Actual: {item}")
    if 'dictionary_item_removed' in diff:
        for item_path, value in diff['dictionary_item_removed'].items():
            messages.append(f"- Unexpected Key in Actual: {item_path} (value: {value})")
    # Value changes
    if 'values_changed' in diff:
        for key, change in diff['values_changed'].items():
            messages.append(f"- Value Mismatch for Key {key}: Expected '{change['old_value']}', Got '{change['new_value']}'")
    # Type changes
    if 'type_changes' in diff:
         for key, change in diff['type_changes'].items():
            messages.append(f"- Type Mismatch for Key {key}: Expected {change['old_type']}, Got {change['new_type']}")

    # List/Iterable changes (Simplified for clarity)
    if 'iterable_item_added' in diff:
        for key, item in diff['iterable_item_added'].items():
             messages.append(f"- Unexpected Item in List {key}: {item}")
    if 'iterable_item_removed' in diff:
        for key, item in diff['iterable_item_removed'].items():
             messages.append(f"- Missing Item in List {key}: {item}")
    # We could add more specific handling for set changes, attribute changes etc. if needed

    return "\n".join(messages) if messages else "No structured differences found (check raw diff for details)."

def run_tests():
    # Define log directory in the current working directory (script root)
    script_dir = Path(__file__).parent # Should be root now
    log_dir = script_dir / "test_results"

    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Setup file logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"test_results_{timestamp}.log"
    log_filepath = log_dir / log_filename # Path object for opening the file
    # Create a path string relative to the presumed workspace root for display
    display_log_path = str(Path("test_results") / log_filename)

    original_stdout = sys.stdout
    log_file = None

    try:
        # Redirect stdout to the log file
        log_file = open(log_filepath, 'w', encoding='utf-8')
        sys.stdout = log_file
        print(f"--- Starting Prompt Evaluation Tests ({timestamp}) ---")
        print(f"Logging results to: {display_log_path}") # Use relative display path

        client = get_openai_client()
        if not client:
            print("\nERROR: Cannot run tests, OpenAI client failed to initialize.")
            # Still print error to original stdout as well
            print("\nERROR: Cannot run tests, OpenAI client failed to initialize.", file=original_stdout)
            sys.exit(1)

        passed = 0
        failed = 0

        for i, test_case in enumerate(TEST_CASES):
            print(f"\n--- Test Case {i+1} --- ")
            print(f"Input Text: {test_case['input']}")

            output_str, _, _, _, r_time, error = call_llm(
                client,
                default_system_prompt,
                default_user_prompt,
                test_case["input"],
                DEFAULT_TEMPERATURE, # Use lower temp for tests
                DEFAULT_MAX_TOKENS,
                TEST_MODEL
            )

            print(f"Response Time: {r_time:.2f}s")

            if error:
                print(f"🛑 FAILED: API Call Error - {error}")
                failed += 1
                continue

            if not output_str:
                print("🛑 FAILED: No output received from LLM.")
                failed += 1
                continue

            try:
                actual_output = json.loads(output_str)
                expected_output = test_case["expected_output"]

                # Print both actual and expected outputs
                print("\nExpected Output (JSON):")
                print(json.dumps(expected_output, indent=2))
                print("\nActual Output (JSON):")
                print(json.dumps(actual_output, indent=2))

                # Use DeepDiff for comparison and reporting
                diff = DeepDiff(expected_output, actual_output, ignore_order=True, report_repetition=True, verbose_level=2)

                if not diff:
                    print("\n✅ PASSED")
                    passed += 1
                else:
                    print("\n🛑 FAILED: Output does not match expected structure.")
                    print("--- Summary of Differences ---")
                    print(format_diff(diff))
                    print("--- Raw DeepDiff ---")
                    print(diff.pretty())
                    print("----------------------")
                    failed += 1

            except json.JSONDecodeError:
                print("\n🛑 FAILED: Output was not valid JSON.")
                print("--- Raw Output ---")
                print(output_str)
                print("------------------")
                failed += 1

        print("\n--- Test Summary ---")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print("--------------------")
        print(f"Test results saved to: {display_log_path}") # Use relative display path

        # Print summary to original console as well
        print(f"\n--- Test Summary ---", file=original_stdout)
        print(f"Passed: {passed}", file=original_stdout)
        print(f"Failed: {failed}", file=original_stdout)
        print(f"Test results saved to: {display_log_path}", file=original_stdout) # Use relative display path
        print("--------------------", file=original_stdout)

    except Exception as e:
        # Print any unexpected errors to both logs and console
        print(f"\n--- UNEXPECTED ERROR DURING TESTING ---", file=log_file if log_file else original_stdout)
        print(f"{e}", file=log_file if log_file else original_stdout)
        import traceback
        traceback.print_exc(file=log_file if log_file else original_stdout)
        print(f"--- END UNEXPECTED ERROR ---", file=log_file if log_file else original_stdout)

        print(f"\n--- UNEXPECTED ERROR DURING TESTING ---", file=original_stdout)
        print(f"{e}", file=original_stdout)
        print("See log file for full traceback.", file=original_stdout)
        print(f"--- END UNEXPECTED ERROR ---", file=original_stdout)

    finally:
        # Ensure stdout is restored and file is closed
        if log_file:
            sys.stdout = original_stdout
            log_file.close()

if __name__ == "__main__":
    run_tests()