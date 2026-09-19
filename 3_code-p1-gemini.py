import os
import argparse
import json
import textwrap
import time
from datetime import datetime, timezone
import google.generativeai as genai

def count_tokens(model: genai.GenerativeModel, text: str) -> int:
    """
    Counts the number of tokens in a given text for the specified Gemini model.
    """
    # The model.count_tokens method returns a CountTokensResponse object.
    # We need to access the .total_tokens attribute to get the integer value.
    response = model.count_tokens(text)
    return response.total_tokens

def get_api_key() -> str | None:
    """
    Retrieves the Google API key.

    It first checks for a 'config.json' file in the script's directory.
    If not found, it falls back to the GOOGLE_API_KEY environment variable.

    Returns:
        The API key string, or None if it's not found in either location.
    """
    # Check for config.json first
    try:
        if os.path.exists("config.json"):
            with open("config.json", 'r') as f:
                config = json.load(f)
                api_key = config.get("GOOGLE_API_KEY")
                if api_key:
                    print("Found API key in config.json.")
                    return api_key
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Could not read or parse config.json: {e}")

    # Fallback to environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("Found API key in environment variables.")
        return api_key
    
    return None


def process_markdown_file(model: genai.GenerativeModel, file_path: str, model_name: str) -> dict | None:
    """
    Reads a Markdown file, sends its content to the Gemini API for analysis,
    and returns the structured data as a dictionary, including model and token info.

    Args:
        model: An initialized Gemini GenerativeModel instance.
        file_path: The path to the Markdown file.
        model_name: The name of the model being used.

    Returns:
        A dictionary with the extracted information, or None if an error occurs.
    """
    start_time_monotonic = time.monotonic()
    start_time_utc = datetime.now(timezone.utc).isoformat()
    
    print(f"Processing file: {os.path.basename(file_path)}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

    # --- 2. Build the prompt ---
    # The system prompt is configured on the model.
    # We just need the user prompt with the paper's content.
    USER_PROMPT = (
        "Please analyse the paper below and return a single JSON object with the extracted metadata.\n"
        "----- BEGIN PAPER -----\n"
        f"{textwrap.dedent(md_text).strip()}\n"
        "----- END PAPER -----"
    )

    input_token_count = count_tokens(model, USER_PROMPT)
    print(f"  - Input token count: {input_token_count}")
    
    # --- 3. Call the API for structured JSON output ---
    try:
        # Configure the model to return JSON directly
        # These are the hyperparameters for the generation
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.2,
            top_p=0.1,
            top_k=1
        )

        response = model.generate_content(
            USER_PROMPT,
            generation_config=generation_config
        )
        
        # --- 4. Parse and validate the structured response ---
        response_text = response.text
        validated_data = json.loads(response_text)
        
        # Basic validation to ensure the response contains the expected keys from the model
        required_keys = ["title", "is_code_used", "reason_code_is_used", 
                         "reason_code_is_not_used",
                         "is_code_publicly_available", 
                         "reason_code_available", "reason_code_unavailable", 
                         "software_used", "programming_language",
                         "cpu_used", "gpu_used", "os_used", "ram_used",
                         "code_link", "code_link_by_the_author", "method_developed"]
        if not all(key in validated_data for key in required_keys):
            print(f"  - Validation Error for {os.path.basename(file_path)}: The model's JSON response is missing required keys.")
            return None
        
        # --- 5. Add script-generated metadata to the output ---
        end_time_monotonic = time.monotonic()
        end_time_utc = datetime.now(timezone.utc).isoformat()
        duration_seconds = end_time_monotonic - start_time_monotonic

        # Add model info, hyperparameters, and token count to the final JSON object.
        validated_data['model_info'] = {
            'model_name': model_name,
            'hyperparameters': {
                'temperature': generation_config.temperature,
                'top_p': generation_config.top_p,
                'top_k': generation_config.top_k
            },
            'input_token_count': input_token_count,
            'processing_time': {
                'start_time_utc': start_time_utc,
                'end_time_utc': end_time_utc,
                'duration_seconds': duration_seconds
            }
        }
            
        return validated_data

    except json.JSONDecodeError as e:
        print(f"  - JSON Decode Error for {os.path.basename(file_path)}: Failed to parse the model's response. {e}")
        print(f"  - Raw response: {response.text}")
    except Exception as e:
        print(f"  - An API or parsing error occurred for {os.path.basename(file_path)}: {e}")

    return None

def main(input_dir: str, output_dir: str):
    """
    Main function to iterate through .md files in an input directory,
    process them with Gemini, and save the results to an output directory.
    """
    api_key = get_api_key()
    if not api_key:
        print("\nFATAL ERROR: Google API key not found.")
        print("Please create a 'config.json' file with {\"GOOGLE_API_KEY\": \"your-key\"}")
        print("or set the GOOGLE_API_KEY environment variable.")
        return

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"Failed to configure Gemini client. Error: {e}")
        return

    # --- System prompt defining the task and the required JSON output structure ---
    SYSTEM_PROMPT = (
        "You are an expert assistant specializing in academic paper computational reproducibility analysis. Your task is to extract "
        "specific metadata about availability from research papers. You must respond with only a valid JSON object, without any additional text, comments, or markdown formatting."
        "The papers are from Transportation Research journals.\n\n"
        "The JSON object must conform to the following schema:\n"
        "{\n"
        '  "title": "string", // The exact title of the paper.\n'
        '  "is_code_used": "boolean", // Did the paper use code to reach its conclusions?\n'
        '  "reason_code_is_used": "string", // **If code was used, you MUST extract the justification directly from the paper. This field MUST contain a VERBATIM quote. Do not summarize or paraphrase.**\n'
        '  "reason_code_is_not_used": "string", // **If code was not used, you MUST extract the justification directly from the paper. This field MUST contain a VERBATIM quote. Do not summarize or paraphrase.**\n'
        '  "is_code_publicly_available": "boolean", // If code was used, is it publicly available?\n'
        '  "reason_code_available": "string", // **If code is available, you MUST extract the justification directly from the paper. This field MUST contain a VERBATIM quote. Do not summarize or paraphrase. For example, if the paper says, \'The code for this project can be found on GitHub\', you must return that exact phrase. If no reason is stated, return an empty string.**\n'
        '  "reason_code_unavailable": "string", // **If code is not available, you MUST extract the reason directly from the paper. If no reason is stated, return an empty string. This field MUST contain a VERBATIM quote. Do not summarize or paraphrase.**\n'
        '  "programming_language": "string", // The programming language used in the paper, if any. If no programming language is mentioned, return an empty string.\n'
        '  "software_used": "string", // The software used in the paper, if any. Do not quote from introduction and references. If no software is mentioned, return an empty string. Note that a programming language is not software.\n'
        '  "cpu_used": "string", // The CPU used in the paper, if any. If no CPU is mentioned, return an empty string.\n'
        '  "gpu_used": "string", // The GPU used in the paper, if any. If no GPU is mentioned, return an empty string.\n'
        '  "os_used": "string", // The operating system used in the paper, if any. If no OS is mentioned, return an empty string.\n'
        '  "ram_used": "string", // The RAM used in the paper, if any. If no RAM is mentioned, return an empty string.\n'
        '  "code_link": "list", // A list of ALL links to the code, including all those used as baselines. If no code is used, return an empty list.\n'
        '  "code_link_by_the_author": "list" // A list of links to the code provided by the authors, excluding those used the others code repos. If no code is provided, return an empty list.\n'
        '  "method_developed": "string" // The method developed in the paper, if any. Be simple and straightforward. If no method is mentioned, return an empty string.\n'
        "}"
    )
    
    # Define the model name
    model_name = "gemini-2.5-flash-lite-preview-06-17"

    # Initialize the Gemini model with the system prompt.
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT
    )

    os.makedirs(output_dir, exist_ok=True)
    print(f"Output will be saved to: {output_dir}")

    for filename in os.listdir(input_dir):
        if filename.endswith(".md"):
            input_path = os.path.join(input_dir, filename)
            # Pass the model_name to the processing function
            result_dict = process_markdown_file(model, input_path, model_name)
            
            if result_dict:
                base_filename = os.path.splitext(filename)[0]
                output_path = os.path.join(output_dir, f"{base_filename}.json")
                
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(result_dict, f, indent=2)
                    print(f"  -> Successfully created JSON: {os.path.basename(output_path)}\n")
                except Exception as e:
                    print(f"  -> Error saving JSON file {output_path}: {e}\n")
        else:
            print(f"Skipping non-Markdown file: {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process Markdown files in a directory to extract reproducibility metadata using Google Gemini's JSON mode.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_dir",
        help="The directory containing the .md files to process."
    )
    parser.add_argument(
        "output_dir",
        help="The directory where the output .json files will be saved."
    )

    args = parser.parse_args()
    main(args.input_dir, args.output_dir)
