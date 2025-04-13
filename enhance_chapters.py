import os
import re # Import regex module for substitution
import google.generativeai as genai
from dotenv import load_dotenv
import time # Import time for potential delays/retries
import argparse # Import argparse for command-line arguments
import asyncio # Import asyncio for parallel processing

# --- Configuration ---
INPUT_DIR = "output/mục_thần_ký_txt"
OUTPUT_DIR = "enhance_output"
PROMPT_FILE = "prompt/translate.prompt.txt"
PROMPT_PLACEHOLDER = "[Dán đoạn văn cần biên tập ở đây]"
GEMINI_MODEL_NAME = "gemini-2.5-pro-exp-03-25" # Using 1.5 Pro as requested

# Cost Configuration (Verify pricing with official Google documentation)
# Prices per 1,000 tokens for gemini-1.5-pro
INPUT_PRICE_PER_1K_TOKENS = 0.0035 # Example price in USD
OUTPUT_PRICE_PER_1K_TOKENS = 0.0105 # Example price in USD
MAX_CUMULATIVE_COST_USD = 5.00 # Cost limit for warnings
CONCURRENT_LIMIT = 10 # Limit the number of concurrent API calls

# --- Load Environment Variables ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
    print("Please ensure it is set in your .env file or environment.")
    exit()

genai.configure(api_key=API_KEY)

# Removed global cumulative_cost

# --- Helper Functions ---

def natural_sort_key(s):
    """Helper function for natural sorting of filenames like 'chapter_10.txt'"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'([0-9]+)', s)]

def read_file_content(filepath):
    """Synchronous file reading (can be called from async)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None

def write_file_content(filepath, content):
    """Synchronous file writing."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True # Indicate success
    except Exception as e:
        print(f"Error writing file {filepath}: {e}")
        return False # Indicate failure

async def call_gemini_api_async(prompt_text, filename):
    """Calls the Gemini API asynchronously and returns content + usage."""
    print(f"[{filename}] Calling Gemini API ({GEMINI_MODEL_NAME})... Length: {len(prompt_text)}")
    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = await model.generate_content_async(prompt_text)

        input_tokens = 0
        output_tokens = 0
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count

        if not response.parts:
             print(f"[{filename}] Warning: Gemini API response did not contain parts. Check safety ratings.")
             print(f"[{filename}] Prompt feedback: {response.prompt_feedback}")
             return None, input_tokens, output_tokens # Return None content but include tokens

        enhanced_text = response.text
        print(f"[{filename}] Gemini API Call Complete.")
        return enhanced_text, input_tokens, output_tokens

    except Exception as e:
        print(f"[{filename}] Error during Gemini API call: {e}")
        return None, 0, 0 # Return None content and 0 tokens on error

async def process_chapter(filename, base_prompt, semaphore):
    """Reads chapter, calls API async, writes file, returns results."""
    input_filepath = os.path.join(INPUT_DIR, filename)
    output_filepath = os.path.join(OUTPUT_DIR, filename)
    write_success = False
    input_tokens = 0
    output_tokens = 0

    async with semaphore: # Limit concurrency
        # Read chapter content (synchronous, but okay within semaphore)
        chapter_content = read_file_content(input_filepath)
        if chapter_content is None:
            return filename, input_tokens, output_tokens, write_success # Return failure

        # Format the full prompt
        full_prompt = re.sub(re.escape(PROMPT_PLACEHOLDER), chapter_content, base_prompt, count=1)

        # Call the Gemini API asynchronously
        enhanced_content, input_tokens, output_tokens = await call_gemini_api_async(full_prompt, filename)

        # Write the file immediately if API call was successful
        if enhanced_content is not None:
            print(f"[{filename}] Writing enhanced content...")
            write_success = write_file_content(output_filepath, enhanced_content)
            if write_success:
                print(f"[{filename}] Successfully wrote enhanced file.")
            else:
                print(f"[{filename}] Failed to write enhanced file.")
        else:
            print(f"[{filename}] Skipping write due to API issue.")

    return filename, input_tokens, output_tokens, write_success

# --- Main Script (Async) ---

async def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Enhance chapter text using Gemini API concurrently.")
    group = parser.add_mutually_exclusive_group() # Ensure conflicting args aren't used together
    group.add_argument("-c", "--chapter", type=str, help="Specify a single chapter filename (e.g., chapter_1337.txt) to process.")
    group.add_argument("-s", "--start-chapter", type=str, help="Specify the filename of the chapter to start processing from.")
    parser.add_argument("-o", "--offset", type=int, help="Number of chapters to process, starting from --start-chapter (requires --start-chapter). Default: process all chapters from start.")
    parser.add_argument("--limit", type=int, default=CONCURRENT_LIMIT, help=f"Maximum number of concurrent API calls (default: {CONCURRENT_LIMIT}).")

    args = parser.parse_args()

    # --- Argument Validation ---
    if args.offset is not None and args.start_chapter is None:
        parser.error("--offset requires --start-chapter to be specified.")
    if args.offset is not None and args.offset <= 0:
        parser.error("--offset must be a positive integer.")
    if args.limit <= 0:
        parser.error("--limit must be a positive integer.")

    # --- Script Start ---

    # 1. Read the base prompt (synchronous)
    base_prompt = read_file_content(PROMPT_FILE)
    if base_prompt is None:
        print(f"Error: Could not read base prompt file at {PROMPT_FILE}. Exiting.")
        return
    if PROMPT_PLACEHOLDER not in base_prompt:
        print(f"Error: Prompt placeholder '{PROMPT_PLACEHOLDER}' not found in {PROMPT_FILE}. Exiting.")
        return

    # 2. Configure Gemini API (already done globally after loading .env)

    # 3. Ensure output directory exists (synchronous)
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"Output directory '{OUTPUT_DIR}' ensured.")
    except Exception as e:
        print(f"Error creating output directory {OUTPUT_DIR}: {e}. Exiting.")
        return

    # 4. Determine files to process (based on args) (synchronous)
    files_to_process = []
    all_files = []
    try:
        # List and naturally sort all potential files first
        all_files_unsorted = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f)) and f.endswith('.txt')]
        all_files = sorted(all_files_unsorted, key=natural_sort_key)
        if not all_files:
            print(f"No .txt files found in {INPUT_DIR}.")
            return
    except FileNotFoundError:
        print(f"Error: Input directory not found at {INPUT_DIR}. Exiting.")
        return
    except Exception as e:
        print(f"Error listing or sorting files in {INPUT_DIR}: {e}. Exiting.")
        return

    # Select files based on arguments
    if args.chapter:
        # Process only the specified chapter
        chapter_filename = args.chapter
        if chapter_filename in all_files:
            files_to_process.append(chapter_filename)
            print(f"Processing specified chapter: {chapter_filename}")
        else:
            print(f"Error: Specified chapter file '{chapter_filename}' not found in {INPUT_DIR}")
            return
    elif args.start_chapter:
        # Process from start chapter, potentially with an offset
        start_filename = args.start_chapter
        try:
            start_index = all_files.index(start_filename)
        except ValueError:
            print(f"Error: Start chapter '{start_filename}' not found in {INPUT_DIR}.")
            return

        if args.offset:
            end_index = start_index + args.offset
            files_to_process = all_files[start_index:end_index]
        else:
            files_to_process = all_files[start_index:]

        if not files_to_process:
            print(f"Warning: No files selected with start chapter '{start_filename}' and offset {args.offset}. Exiting.")
            return
        print(f"Selected {len(files_to_process)} chapters to process starting from {start_filename}" + (f" with offset {args.offset}." if args.offset else "."))

    else:
        # Process all .txt files in the input directory (default behavior)
        files_to_process = all_files
        print(f"Selected all {len(files_to_process)} chapters found in {INPUT_DIR} for processing.")

    # 5. Create and run tasks concurrently
    semaphore = asyncio.Semaphore(args.limit)
    tasks = [process_chapter(filename, base_prompt, semaphore) for filename in files_to_process]
    print(f"\nStarting concurrent processing of {len(tasks)} chapters with limit {args.limit}...")
    results = await asyncio.gather(*tasks)
    print("\n...Concurrent processing finished.")

    # 6. Process results and calculate costs
    print("\nCalculating final costs...")
    cumulative_cost = 0.0
    processed_count = 0
    skipped_count = 0

    for filename, input_tokens, output_tokens, write_success in results:

        # Calculate cost for this specific result
        input_cost = (input_tokens / 1000) * INPUT_PRICE_PER_1K_TOKENS
        output_cost = (output_tokens / 1000) * OUTPUT_PRICE_PER_1K_TOKENS
        call_cost = input_cost + output_cost
        limit_exceeded_before = cumulative_cost >= MAX_CUMULATIVE_COST_USD
        cumulative_cost += call_cost
        limit_exceeded_after = cumulative_cost >= MAX_CUMULATIVE_COST_USD

        # Log cost details for this chapter
        print(f"\n--- Result for: {filename} ---")
        print(f"  Input Tokens : {input_tokens}")
        print(f"  Output Tokens: {output_tokens}")
        print(f"  Estimated Cost: ${call_cost:.6f}")
        print(f"  Cumulative Cost: ${cumulative_cost:.6f}")
        if limit_exceeded_after:
            print(f"  *** Warning: Cumulative cost limit (${MAX_CUMULATIVE_COST_USD:.2f}) is exceeded! ***")
        print(f"---------------------------")

        if write_success:
            processed_count += 1
        else:
            skipped_count += 1

    print(f"\n--- Script finished ---")
    print(f"Total chapters processed: {processed_count}")
    print(f"Total chapters skipped : {skipped_count}")
    print(f"Final Estimated Cumulative Cost: ${cumulative_cost:.6f}")
    if cumulative_cost >= MAX_CUMULATIVE_COST_USD:
        print(f"*** Warning: Final cumulative cost exceeded the limit of ${MAX_CUMULATIVE_COST_USD:.2f} ***")


if __name__ == "__main__":
    asyncio.run(main()) 