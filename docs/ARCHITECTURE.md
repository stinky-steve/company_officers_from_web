# ARCHITECTURE.md

This document provides a high-level overview of the **Management Names Extraction Pipeline**. The pipeline processes ~150,000 JSON files (containing mining company website content) to extract names of management personnel and their roles. It is implemented in Python and containerized with Docker for portability and reproducibility.

## Overview

- **Purpose:** Transform unstructured web content into structured data by identifying management team members (names) and their roles/titles in each document.
- **Input:** A large collection of JSON files (~150k) where each JSON contains text from a mining company's website (e.g. "About Us" or "Leadership Team" pages).
- **Output:** A consolidated structured dataset (e.g. CSV or JSON) listing the extracted names and roles for each source (often each company or page).
- **Processing:** Uses a Large Language Model (LLM) to perform natural language extraction of names and roles from the unstructured text, due to the varied formats of websites.

## High-Level Data Flow

1. **Data Ingestion:** The pipeline reads JSON files from an input directory. Each file is parsed to retrieve the relevant text content (and metadata like company name or URL if needed).
2. **Preprocessing:** Minimal cleaning or filtering is applied to the text (e.g. removing HTML tags if present, trimming whitespace). Optionally, the pipeline can skip pages unlikely to contain management info (using keyword filters like "CEO", "Officer", "Director" etc.) to save processing time.
3. **LLM Extraction:** For each page's text, the pipeline constructs a prompt (using a predefined template) and queries an LLM (such as OpenAI's GPT model) to extract **Name – Role** pairs. The prompt guides the model to output just the structured information (see **PROMPTS.md** for details).
4. **Post-processing:** The LLM's response is parsed (e.g. from JSON or formatted text) to obtain the list of names and roles. These are then aggregated or stored along with identifiers (such as the source file name or company).
5. **Output Storage:** Extracted results from all files are written to an output file or database (for example, a CSV file with columns for company/page, person name, and role). This output can then be used for further analysis.

## Components and Responsibilities

- **Data Loader (Ingestion Module):** Responsible for scanning the input directory and reading each JSON file. It handles JSON parsing and retrieves fields like the page text. This module ensures memory-efficient reading (processing one file at a time) due to the large number of files.
- **Preprocessor:** Cleans or normalizes text if necessary. For example, if the JSON contains HTML content, this component strips HTML tags (using a library like BeautifulSoup if needed) to yield plain text. It may also perform an optional **filtering step** to detect if the page contains keywords related to management (to decide if it should proceed to extraction).
- **LLM Extractor:** Encapsulates the logic for interacting with the Large Language Model. It loads the prompt template (from `PROMPTS.md` or an embedded string in the code), fills in the page content, and calls the LLM API. This component also handles API communication (via the OpenAI Python library or similar) and error handling (e.g., rate limiting or retry on failures).
- **Result Parser:** Takes the raw LLM response and converts it into structured data. For example, if the LLM returns JSON text, this parser will `json.loads` it into Python objects. If the LLM returns a simple text list, the parser will split or regex-match the names and roles. This component ensures the output is normalized (consistent formatting of names and roles).
- **Output Writer:** Responsible for writing the extracted data to persistent storage. This could accumulate results in memory and write a single CSV/JSON at the end, or stream results to a file as they are extracted. It adds any necessary context to each record (such as the source file name or company name from the JSON metadata) before writing.
- **Orchestration (Pipeline Controller):** The main script or controller that ties all the above pieces together. It iterates over files, calls the loader, then passes content to the preprocessor, then to the LLM extractor, and collects results through the parser into the writer. It also manages parallelism (if implemented) and overall workflow control (start, finish, logging progress).

## Code Structure

The code is organized to reflect the above components, making it easy to maintain and understand:

- **`src/pipeline.py`:** The main pipeline script that orchestrates the end-to-end process (could also be named `run_pipeline.py` or similar). It uses the other modules to perform each stage in sequence.
- **`src/data_reader.py`:** Contains functions to read JSON files and extract the text content (and any needed metadata). This corresponds to the Data Loader.
- **`src/llm_extractor.py`:** Contains the LLM interaction logic. For example, a function `extract_names_roles(text: str) -> list` that formats the prompt and calls the OpenAI API, returning a parsed list of names and roles.
- **`src/output_writer.py`:** Contains helper functions to write outputs (e.g., appending to a CSV or JSON file). Could handle opening/closing files and writing header if needed.
- **`prompts/` or `docs/PROMPTS.md`:** (Documentation/asset) Contains the prompt templates used by `llm_extractor.py`. In this project, prompt templates and examples are documented in **PROMPTS.md** for reference.
- **`Dockerfile`:** Specifies the Docker image setup (Python environment, installing dependencies, copying the above source code). Ensures the pipeline runs in a controlled environment with all required tools (see **TECH_STACK.md** for details).

All components are containerized together, meaning the Docker container includes the Python runtime and all needed libraries. The input JSON files are mounted into the container at runtime, and output is written to a mounted volume, so data persists on the host.

## Architectural Considerations

- **Scalability:** Processing 150k files can be time-consuming, especially with LLM API calls. The architecture supports horizontal scaling by allowing multiple containers or processes to run on different subsets of the data (for example, splitting the input files directory and running the pipeline in parallel). Within a single run, the pipeline could also use multi-threading or async calls to utilize the LLM API concurrently (throttled to respect rate limits).
- **Reliability:** The pipeline is designed to handle exceptions gracefully. If the LLM call fails or times out for a particular file, the error is caught; the pipeline can log the issue and optionally retry or skip that file, continuing with the rest of the data. This ensures a long-running batch job won't crash due to a single problematic input or transient API issue.
- **Maintainability:** By separating responsibilities into distinct modules (as outlined above), each part of the system can be developed and tested in isolation. For instance, you can unit test the JSON parsing or the prompt formatting logic separately. The **ARCHITECTURE.md** (this document) serves as a guide for new contributors to quickly locate the part of code responsible for a certain functionality.
- **Extensibility:** The architecture allows for swapping out the LLM or changing the prompt without affecting the rest of the pipeline. For example, if a new model or a different prompt format yields better results, the change would be localized to the LLM extractor component. Similarly, additional preprocessing (like language translation or text splitting for very large content) can be inserted if needed without major overhaul.
- **Data Volume Handling:** The system does not load all 150k files into memory at once. It streams through files one by one (or in manageable batches) to keep memory usage constant. Intermediate results can be written incrementally to avoid holding the entire output in memory as well.

Overall, this high-level design ensures that the pipeline is robust, scalable, and easy to work with for extracting management names and roles from a large corpus of unstructured text data. 