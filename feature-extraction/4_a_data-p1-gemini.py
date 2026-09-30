import os
import argparse
import json
import textwrap
import time
from datetime import datetime, timezone
import google.generativeai as genai

# --- NEW: Function to read the prompt from a file ---
def read_prompt_from_file(file_path: str) -> str | None:
    """
    Reads the content of the prompt file.
    
    Returns:
        The prompt string, or None if the file cannot be read.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"FATAL ERROR: Prompt file not found at '{file_path}'")
        return None
    except Exception as e:
        print(f"FATAL ERROR: Could not read prompt file '{file_path}': {e}")
        return None

def count_tokens(model: genai.GenerativeModel, text: str) -> int:
    """
    Counts the number of tokens in a given text for the specified Gemini model.
    """
    response = model.count_tokens(text)
    return response.total_tokens

def get_api_key() -> str | None:
    """
    Retrieves the Google API key.
    """
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

    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("Found API key in environment variables.")
        return api_key
    
    return None

def process_markdown_file(model: genai.GenerativeModel, file_path: str, model_name: str) -> dict | None:
    """
    Reads a Markdown file, sends its content to the Gemini API for analysis,
    and returns the structured data as a dictionary, including model and token info.
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

    USER_PROMPT = (
        "Please analyse the paper below and return a single JSON object with the extracted metadata.\n"
        "----- BEGIN PAPER -----\n"
        f"{textwrap.dedent(md_text).strip()}\n"
        "----- END PAPER -----"
    )

    input_token_count = count_tokens(model, USER_PROMPT)
    print(f"  - Input token count: {input_token_count}")
    
    try:
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0,
            top_p=0.1,
            top_k=1,
            max_output_tokens=5000
        )

        response = model.generate_content(
            USER_PROMPT,
            generation_config=generation_config
        )
        
        response_text = response.text
        validated_data = json.loads(response_text)

        # required_keys = ["title", "is_data_used", "is_simulation_study", "reason_data_is_used", 
        #                 "is_data_repository_available", "reason_data_repository_available", "links_to_the_data_repository", 
        #                 "is_data_cited_or_linked", "reason_data_cited_or_linked", "links_to_the_data_cited_or_linked"]

        # required_keys = ["title", "is_data_used", "is_simulation_study",  
        #                  "is_data_repository_available", "links_to_the_data_repository", 
        #                  "is_data_cited_or_linked", "links_to_the_data_cited_or_linked"]
        

        # if not all(key in validated_data for key in required_keys):
        #     print(f"  - Validation Error for {os.path.basename(file_path)}: The model's JSON response is missing required keys.")
        #     return None
        
        end_time_monotonic = time.monotonic()
        end_time_utc = datetime.now(timezone.utc).isoformat()
        duration_seconds = end_time_monotonic - start_time_monotonic

        validated_data['model_info'] = {
            'model_name': model_name,
            'hyperparameters': {
                'temperature': generation_config.temperature,
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

        #save response.text to a txt file for debugging
        error_file_path = os.path.join(os.path.dirname(file_path), f"errors/error_response_{os.path.basename(file_path)}.txt")
        # import pdb; pdb.set_trace()
        with open(error_file_path, 'w', encoding='utf-8') as error_file:
            error_file.write(response.text)
    except Exception as e:
        print(f"  - An API or parsing error occurred for {os.path.basename(file_path)}: {e}")

    return None

# --- MODIFIED: main function now accepts a prompt_file path ---
def main(input_dir: str, output_dir: str, prompt_file: str):
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

    # --- MODIFIED: Read system prompt from the external file ---
    system_prompt_text = read_prompt_from_file(prompt_file)
    if not system_prompt_text:
        return # Exit if the prompt file could not be read.
    
    # --- DELETED: The hardcoded SYSTEM_PROMPT string is now gone ---

    model_name = "gemini-2.5-flash-lite-preview-06-17"

    # --- MODIFIED: Initialize the model with the prompt text we read from the file ---
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt_text
    )

    os.makedirs(output_dir, exist_ok=True)
    print(f"Output will be saved to: {output_dir}")

    for filename in os.listdir(input_dir):
        if filename.endswith(".md"):
            if os.path.exists(os.path.join(output_dir, filename.replace(".md", ".json"))):
                print(f"{filename} has already been processed! Skipping...")
                continue

            input_path = os.path.join(input_dir, filename)
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
    parser.add_argument(
        "--prompt-file",
        default="4_b_data-prompt.md",
        help="Path to the Markdown file containing the system prompt. (default: data-prompt.md)"
    )

    args = parser.parse_args()
    main(args.input_dir, args.output_dir, args.prompt_file)