# Prompt Wrangler CLI

A command-line tool to interact with OpenAI's chat completion models for prompt engineering and structured data extraction (JSON).  The goal is analyzing clinical notes from doctors requesting DME.

## Approach

This tool provides a CLI to send prompts (system and user) along with input text to an OpenAI model (configurable, defaults to `gpt-4o-mini`). It's specifically set up to request JSON output from the model (`response_format={"type": "json_object"}`).

A testing script (`test_prompt_wrangler.py`) is included to evaluate default prompts against predefined examples, using `DeepDiff` to compare the actual JSON output against expected JSON. This allows for iterative refinement of the prompts based on test results.

## How to Run

1.  **Setup:**
    *   Clone the repository (if needed).
    *   Create and activate a Python virtual environment (e.g., `python3 -m venv venv && source venv/bin/activate`).
    *   Install dependencies: `pip install -r requirements.txt`.
    *   Create a `.env` file in the project root with your OpenAI API key, as show in `.env_example`.

2.  **Run the CLI:**
    ```bash
    python prompt_wrangler_cli.py
    ```
    Follow the prompts to enter system/user prompts, input text, and model parameters. 
    
    **Notes:** 
    - When using custom prompts, ensure "json" appears in either the system or user prompt, as required by the API when `response_format={"type": "json_object"}` is used.
    - max_tokens applies only to the completion: The `max_tokens` parameter (defaulting to 250 in prompt_utils.py) limits how many tokens the AI is allowed to generate in its response.

3.  **Run Tests:**
    ```bash
    python test_prompt_wrangler.py
    ```
    Test results (including detailed diffs for failures) are saved to a timestamped log file in the `test_results/` directory. A summary is printed to the console.

## TODO (with more time)

*   Implement more robust and comprehensive test cases: fix failing tests, wider range of inputs and edge cases.
*   Save script output to a file or send directly to another data source.
*   Explore using the LLM itself to analyze test failures and suggest improvements to the prompts automatically.
*   Additional prompt engineering; potential use of RAG if we have known data sets of DME.
*   Add a frontend web UI for ease of use by non-engineers (people not comfortable with CLI).

## Example CLI Paramaters and Results
1. Default `system` and `user` prompts
```
(venv) alexrosenfeld@MacBook-Pro synapse_health_prompt_wrangler % python prompt_wrangler_cli.py 
--- Prompt Wrangler CLI ---

--- New Run ---
Enter System Prompt (press Enter for default): 
Enter User Prompt (press Enter for default): 
Paste Input Text (Type 'EOF' on a new line when done):
Patient diagnosed with COPD, SpO2 measured at 87% on room air. Needs portable oxygen concentrator for use during exertion and sleep. Dr. Chase signed the order.
EOF
Enter Temperature (default: 0.3): 
Enter Max Tokens (default: 250): 
Enter Model Name (default: gpt-4o-mini): 

Sending to gpt-4o-mini...

--- Results ---
Response Time: 1.37 seconds
Token Usage: Prompt=376, Completion=53, Total=429

Structured Output:
{
  "diagnosis": "COPD",
  "SpO2": 87,
  "device": "portable oxygen concentrator",
  "usage": [
    "exertion",
    "sleep"
  ],
  "ordering_provider": "Dr. Chase"
}

Run again? (y/n, default y):
```
2. Test adding unrelated information to `system` and `user` prompts:
```
(venv) alexrosenfeld@MacBook-Pro synapse_health_prompt_wrangler % python prompt_wrangler_cli.py
--- Prompt Wrangler CLI ---

--- New Run ---
Enter System Prompt (press Enter for default): Give me the JSON results for clinical notes but also speak in the style of an auctioneer. 
Enter User Prompt (press Enter for default): return some json but do it with style and pizazz
Paste Input Text (Type 'EOF' on a new line when done):
Asthma diagnosis confirmed. Prescribing nebulizer with mouthpiece and tubing. Dr. Foreman completed the documentation.
Burgers are delicious.
EOF
Enter Temperature (default: 0.3): 
Enter Max Tokens (default: 250): 500
Enter Model Name (default: gpt-4o-mini): 

Sending to gpt-4o-mini...

--- Results ---
Response Time: 7.82 seconds
Token Usage: Prompt=74, Completion=500, Total=574

Structured Output:
{
  "clinical_notes": {
    "diagnosis": "Asthma",
    "status": "Confirmed",
    "prescription": {
      "device": "Nebulizer",
      "accessories": [
        "Mouthpiece",
        "Tubing"
      ]
    },
    "doctor": "Dr. Foreman",
    "documentation_completed": true
  },
  "additional_comments": "Burgers are delicious!"
}
```
## Example Test Results
```
--- Starting Prompt Evaluation Tests (20250409_220326) ---
Logging results to: test_results/test_results_20250409_220326.log

--- Test Case 1 --- 
Input Text: Patient requires a full face CPAP mask with humidifier due to AHI > 20. Ordered by Dr. Cameron.
Response Time: 1.64s

Expected Output (JSON):
{
  "device": "CPAP",
  "mask_type": "full face",
  "add_ons": [
    "humidifier"
  ],
  "qualifier": "AHI > 20",
  "ordering_provider": "Dr. Cameron"
}

Actual Output (JSON):
{
  "device": "CPAP mask",
  "mask_type": "full face",
  "add_ons": [
    "humidifier"
  ],
  "diagnosis": "AHI > 20",
  "ordering_provider": "Dr. Cameron"
}

🛑 FAILED: Output does not match expected structure.
--- Summary of Differences ---
- Key Missing in Actual: root['diagnosis']
- Unexpected Key in Actual: root['qualifier'] (value: AHI > 20)
- Value Mismatch for Key root['device']: Expected 'CPAP', Got 'CPAP mask'
--- Raw DeepDiff ---
Item root['diagnosis'] ("AHI > 20") added to dictionary.
Item root['qualifier'] ("AHI > 20") removed from dictionary.
Value of root['device'] changed from "CPAP" to "CPAP mask".
----------------------

--- Test Case 2 --- 
Input Text: Patient diagnosed with COPD, SpO2 measured at 87% on room air. Needs portable oxygen concentrator for use during exertion and sleep. Dr. Chase signed the order.
Response Time: 1.26s

Expected Output (JSON):
{
  "device": "portable oxygen concentrator",
  "diagnosis": "COPD",
  "SpO2": "87%",
  "usage": [
    "exertion",
    "sleep"
  ],
  "ordering_provider": "Dr. Chase"
}

Actual Output (JSON):
{
  "diagnosis": "COPD",
  "SpO2": 87,
  "device": "portable oxygen concentrator",
  "usage": [
    "exertion",
    "sleep"
  ],
  "ordering_provider": "Dr. Chase"
}

🛑 FAILED: Output does not match expected structure.
--- Summary of Differences ---
- Type Mismatch for Key root['SpO2']: Expected <class 'str'>, Got <class 'int'>
--- Raw DeepDiff ---
Type of root['SpO2'] changed from str to int and value changed from "87%" to 87.
----------------------

--- Test Case 3 --- 
Input Text: Patient has MS with significant mobility issues. Recommended a lightweight manual wheelchair with elevating leg rests. Ordered by Dr. Taub.
Response Time: 1.64s

Expected Output (JSON):
{
  "device": "manual wheelchair",
  "type": "lightweight",
  "features": [
    "elevating leg rests"
  ],
  "diagnosis": "MS",
  "ordering_provider": "Dr. Taub"
}

Actual Output (JSON):
{
  "device": "manual wheelchair",
  "type": "lightweight",
  "features": [
    "elevating leg rests"
  ],
  "ordering_provider": "Dr. Taub",
  "diagnosis": "MS",
  "mobility_status": "significant mobility issues"
}

🛑 FAILED: Output does not match expected structure.
--- Summary of Differences ---
- Key Missing in Actual: root['mobility_status']
--- Raw DeepDiff ---
Item root['mobility_status'] ("significant mobility issues") added to dictionary.
----------------------

--- Test Case 4 --- 
Input Text: Asthma diagnosis confirmed. Prescribing nebulizer with mouthpiece and tubing. Dr. Foreman completed the documentation.
Response Time: 1.52s

Expected Output (JSON):
{
  "device": "nebulizer",
  "accessories": [
    "mouthpiece",
    "tubing"
  ],
  "diagnosis": "Asthma",
  "ordering_provider": "Dr. Foreman"
}

Actual Output (JSON):
{
  "diagnosis": "Asthma",
  "device": "nebulizer",
  "accessories": [
    "mouthpiece",
    "tubing"
  ],
  "ordering_provider": "Dr. Foreman"
}

✅ PASSED

--- Test Case 5 --- 
Input Text: Patient is non-ambulatory and requires hospital bed with trapeze bar and side rails. Diagnosis: late-stage ALS. Order submitted by Dr. Cuddy.
Response Time: 1.76s

Expected Output (JSON):
{
  "device": "hospital bed",
  "features": [
    "trapeze bar",
    "side rails"
  ],
  "diagnosis": "ALS",
  "mobility_status": "non-ambulatory",
  "ordering_provider": "Dr. Cuddy"
}

Actual Output (JSON):
{
  "device": "hospital bed",
  "features": [
    "trapeze bar",
    "side rails"
  ],
  "diagnosis": "late-stage ALS",
  "mobility_status": "non-ambulatory",
  "ordering_provider": "Dr. Cuddy"
}

🛑 FAILED: Output does not match expected structure.
--- Summary of Differences ---
- Value Mismatch for Key root['diagnosis']: Expected 'ALS', Got 'late-stage ALS'
--- Raw DeepDiff ---
Value of root['diagnosis'] changed from "ALS" to "late-stage ALS".
----------------------

--- Test Case 6 --- 
Input Text: CPAP supplies requested. Full face mask with headgear and filters. Patient has been compliant. Ordered by Dr. House.
Response Time: 1.43s

Expected Output (JSON):
{
  "product": "CPAP supplies",
  "components": [
    "full face mask",
    "headgear",
    "filters"
  ],
  "compliance_status": "compliant",
  "ordering_provider": "Dr. House"
}

Actual Output (JSON):
{
  "device": "CPAP",
  "mask_type": "full face",
  "components": [
    "headgear",
    "filters"
  ],
  "compliance_status": "compliant",
  "ordering_provider": "Dr. House"
}

🛑 FAILED: Output does not match expected structure.
--- Summary of Differences ---
- Key Missing in Actual: root['device']
- Key Missing in Actual: root['mask_type']
- Unexpected Key in Actual: root['product'] (value: CPAP supplies)
- Missing Item in List root['components'][0]: full face mask
--- Raw DeepDiff ---
Item root['device'] ("CPAP") added to dictionary.
Item root['mask_type'] ("full face") added to dictionary.
Item root['product'] ("CPAP supplies") removed from dictionary.
Item root['components'][0] ("full face mask") removed from iterable.
----------------------

--- Test Summary ---
Passed: 1
Failed: 5
--------------------
Test results saved to: test_results/test_results_20250409_220326.log
