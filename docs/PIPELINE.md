# PIPELINE.md

This document describes the step-by-step processing logic of the pipeline. It provides a walkthrough of how data flows through the system, with code-style pseudocode and comments to clarify each step. Developers can use this as a blueprint while implementing or reviewing the pipeline code.

## Pipeline Steps Overview

1. **Initialization:**
   - Load configuration (if any) and set up environment (e.g., API keys from environment variables, input/output paths).
   - Import necessary modules (data reader, LLM extractor, etc.) and initialize any global resources (like opening output file, setting up logging).
2. **Input Discovery:**
   - Scan the input data directory for JSON files. Create a list of file paths to process (e.g., using Python's `os.listdir` or `glob`).
   - (Optional) Shuffle or sort the list if needed (shuffling can distribute load more evenly if running parallel instances).
3. **Processing Loop:**
   - Iterate over each JSON file in the list:
     - Read the JSON file into a Python dict (using `json` library).
     - Extract the relevant text content field (e.g., `content` or `text` field that contains the page's text). Also retrieve metadata like company name or URL if present (for context or output).
     - **Filtering:** If the content is empty or does not contain any keywords suggesting management info, skip to the next file (this saves time and API calls).
     - Prepare the LLM prompt by inserting the content into the prompt template (as documented in **PROMPTS.md**). Ensure the content is truncated if it exceeds model length limits (e.g., for very large pages, you might only send the first N characters or split into chunks).
     - Call the LLM API with the prompt (using the OpenAI SDK or equivalent). Await or retrieve the LLM's completion which should ideally be a structured list of names and roles.
     - Parse the LLM response to extract the names and roles. This could involve loading a JSON string or splitting lines, depending on the response format.
     - If names/roles are found, format and write them to the output (e.g., one line per name in a CSV, including the source identifier). If none are found, you may still record that the page had no result (or simply omit it from output).
4. **Post-Processing and Cleanup:**
   - After looping through all files, finalize the output. For example, close the output CSV file and write any summary or footer if needed.
   - Log a summary of extraction (e.g., how many names were found, how many pages processed/skipped) for reference.
   - Any allocated resources are cleaned up (close files, etc.). If using external APIs, ensure any client sessions are closed if required.

5. **Result Verification (Optional):**
   - Optionally, run a verification step or spot-check some outputs to ensure the format is correct (especially if JSON output is expected, verify the JSON is well-formed).
   - This is not an automated pipeline step, but a good practice after pipeline runs.

Each of these steps can be mapped to sections in the code. Below is pseudocode illustrating the above logic in a linear fashion:

```python
import os, json
from src import data_reader, llm_extractor, output_writer  # hypothetical module imports

# Initialization
INPUT_DIR = "/app/data/input"   # where JSON files are mounted in Docker
OUTPUT_FILE = "/app/data/output/management_extraction.csv"
API_KEY = os.getenv("OPENAI_API_KEY")  # API key for LLM, ensure it's set
model_name = "gpt-4"  # or "gpt-3.5-turbo", could be configurable

# Open output file and write header
out_f = open(OUTPUT_FILE, "w", encoding="utf-8")
out_f.write("source, name, role\n")

# Iterate over input files
for filename in os.listdir(INPUT_DIR):
    if not filename.endswith(".json"):
        continue
    file_path = os.path.join(INPUT_DIR, filename)
    data = json.load(open(file_path, 'r', encoding='utf-8'))
    text = data.get("content") or data.get("text") or ""
    company = data.get("company") or data.get("company_name") or data.get("url", "")
    
    # Skip if content is empty or too short
    if not text or len(text.strip()) == 0:
        continue
    
    # Optional: Keyword filtering to skip irrelevant pages
    if not any(word in text.lower() for word in ["chief", "officer", "director", "president", "leadership", "management"]):
        # If none of these keywords present, likely no management info
        continue
    
    # Prepare prompt (insert the page content into the template)
    prompt = PROMPT_TEMPLATE.format(content=text[:5000])  # truncate if necessary to 5000 chars (example)
    
    # Call LLM API to get extraction
    try:
        response = llm_extractor.query_llm(prompt, model=model_name, api_key=API_KEY)
    except Exception as e:
        # Handle API errors (e.g., log and skip this file)
        print(f"LLM API error for {filename}: {e}")
        continue
    
    # Parse LLM response
    try:
        results = llm_extractor.parse_response(response)
    except Exception as e:
        print(f"Failed to parse response for {filename}: {e}")
        continue
    
    # Write results to CSV
    for name, role in results:
        # Ensure commas or newlines in fields are handled (e.g., quote if CSV)
        out_f.write(f"{company},{name},{role}\n")
# end for

# Cleanup
out_f.close()
print("Extraction complete. Output saved to", OUTPUT_FILE)
```

*The above pseudocode illustrates the core logic.* In an actual implementation, `llm_extractor.query_llm` would internally use something like `openai.ChatCompletion.create()` or a similar function to call the model, and `parse_response` would handle the model's output format (for instance, parsing JSON text). We also truncate the content (`text[:5000]`) as a safe measure to keep prompts within token limits – in practice, one might use model-specific token counting (via libraries like `tiktoken`) to ensure the prompt is within limits (e.g., 8192 tokens for GPT-4).

## Parallel Processing (Optional)

For 150k files, a single-threaded loop might be slow. The pipeline can be extended to use parallel processing:
- **Multi-threading or Multi-processing:** Using Python's `concurrent.futures.ThreadPoolExecutor` or `ProcessPoolExecutor` to process multiple files simultaneously. For example, spawn N worker threads, each handling a subset of files. Care must be taken with rate-limiting the LLM API (e.g., OpenAI's rate limits) when doing this.
- **Batching API Calls:** If the LLM or service supports batch processing (processing multiple texts in one API call), that could greatly speed up the pipeline. (For instance, sending a batch of 5 pages' content in one request and getting 5 outputs, though the OpenAI API doesn't natively support multi-prompt batches in one call for chat completions – so likely sticking to one call per file.)
- **Running Multiple Containers:** Another approach is to split the input dataset into chunks and run multiple Docker containers in parallel (each with its own subset of files and separate API key or appropriate rate throttling). The output from all can then be combined. This isn't handled within the code itself but is an operational strategy.

If parallelism is introduced, the code structure might change (for example, using asynchronous calls with `asyncio` and `openai.AsyncConfiguration`). This pipeline is initially written in a simple form for clarity, but can be optimized as needed.

## Error Handling & Logging

Throughout the pipeline, robust error handling is vital for a long-running job:
- JSON parsing errors (malformed file) are caught and logged, with the file skipped.
- LLM API errors or timeouts: use try/except around the API call. If an error occurs, the pipeline could retry a few times (with exponential backoff) or log and skip. All such events are recorded (possibly in a log file or stdout).
- Parsing errors: if the LLM returns something unexpected (not following the format), the parser should handle `JSONDecodeError` or formatting issues. In some cases, a simple heuristic could clean the response (e.g., strip non-JSON parts) and retry parsing.
- Each major step could output a log message. If running inside Docker via command line, these logs will appear in the console. For example: "Processing file X...", "No relevant content, skipping file Y.", "Extracted 3 names from file Z." etc. This helps track progress given the large number of files.

## Pseudocode Explanation

The pseudocode above is annotated with comments (`# ...`) to serve as an inline explanation of each part:
- Comments starting with **Step** indicate major pipeline phases.
- Comments within the loop explain what each block is doing (loading data, filtering, prompting the LLM, etc.).
- The use of high-level function calls like `llm_extractor.query_llm` abstracts the details of making the API call, keeping the pipeline logic readable. The actual implementation would handle constructing the `openai.ChatCompletion` request.
- Writing to CSV is shown for clarity. In practice, one might use Python's `csv` module or Pandas for convenience, but writing manually as shown is straightforward for simple outputs.

Developers can use this outline to implement the actual code. It's structured in a way that aligns with the component breakdown from the architecture. By following this, one ensures that the code remains organized and each part of the pipeline is clearly delineated. 