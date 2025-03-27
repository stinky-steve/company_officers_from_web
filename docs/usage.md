# USAGE.md

This guide explains how to build and run the Docker-based pipeline, how to provide the input data, and how to retrieve the outputs. Following these instructions will allow you to execute the extraction process on your own machine or server.

## Prerequisites

- **Docker Installed:** Ensure you have Docker Engine installed on your system. Verify by running `docker --version`.
- **OpenAI API Key:** Obtain an API key from OpenAI (if using their LLM service) and keep it handy. Charges may apply for API usage, so ensure you have access to the service.
- **Project Files:** You should have the project repository, which includes the Dockerfile, source code, and docs. If not, clone the repository from the source control.

## Building the Docker Image

Before running the pipeline, build the Docker image to package the code and environment. In the project directory (where the `Dockerfile` is located), run:

```bash
docker build -t management-extractor:latest .
```

This command will:
- Use the provided Dockerfile to create an image.
- Install Python and all required Python libraries (from `requirements.txt` or similar setup in the Dockerfile).
- Set up the container to run the pipeline (for example, the Dockerfile might use `CMD ["python", "src/pipeline.py"]` to define the default execution).

The `-t management-extractor:latest` tags the image with a name for easier reference when running.

*(Note: You may need internet access during the build to download Python packages. Once built, the image is self-contained.)*

## Preparing Input and Output Directories

You should have a directory containing the input JSON files. Let's assume:
- Input JSON files are located on your host machine at `/path/to/input_jsons` (this directory could contain subfolders or just a lot of .json files).
- You have an output directory on your host, e.g. `/path/to/output`, where you want the results to be saved.

No special preparation of files is needed beyond having them in a directory. Ensure the output directory is empty or ready to receive new output (existing files won't be overwritten unless they have the same name, e.g., if we output `management_extraction.csv`, remove or archive any old copy).

## Running the Pipeline Container

Use Docker's run command to start the container, mounting the input and output directories and providing the API key:

```bash
docker run --rm \
  -v /path/to/input_jsons:/app/data/input:ro \
  -v /path/to/output:/app/data/output:rw \
  -e OPENAI_API_KEY=<your-openai-api-key> \
  management-extractor:latest
```

Explanation of the options:
- `--rm`: Automatically remove the container after it finishes. This keeps things tidy since we don't need to keep the container instance around after running.
- `-v /path/to/input_jsons:/app/data/input:ro`: This mounts the host's input directory into the container. Inside the container, `/app/data/input` will refer to the host's input files. We use `:ro` (read-only) to ensure the container doesn't modify the input data.
- `-v /path/to/output:/app/data/output:rw`: Mounts the host output directory into the container at `/app/data/output`. The pipeline will write results here. `:rw` gives it write permission.
- `-e OPENAI_API_KEY=...`: Sets the environment variable `OPENAI_API_KEY` inside the container. The pipeline picks up the API key from this environment variable to authenticate with OpenAI. (Replace `<your-openai-api-key>` with the actual key string. Alternatively, you can set this variable in your shell and use `-e OPENAI_API_KEY` without the value to forward it.)
- `management-extractor:latest`: This is the image name we built. Docker will create a container from this image and run it.

When the container runs, it should start executing the pipeline immediately (because the Dockerfile's CMD points to the pipeline script). You will see logs in the console. For example, it might log progress like:
```
Processing file 1 of 150000: company123_leadership.json
... extracted 5 names
Processing file 2 of 150000: companyXYZ_team.json
... no management info found, skipping
...
```
(It depends on how logging is implemented in the code.)

The pipeline may take a long time for 150k files, especially if using the LLM API sequentially. You can monitor the logs. If needed, you can run multiple instances with different subsets of data (see **Scaling** below).

## During Execution

- **Monitoring**: You can open another terminal to check the output directory. If the pipeline writes incrementally, you might see an output file (e.g., `management_extraction.csv`) growing in size. Avoid opening the file for writing; if you want to check it, open a copy.
- **Logs**: All printouts from the script will appear in the `docker run` console. If you need to capture these, you can redirect them to a file by adding `> run.log` after the command.
- **Performance**: If you notice it's slow, ensure your machine has enough resources. The Docker container will use CPU and memory for both Python and the network calls to the API. Using GPT-3.5 might be faster than GPT-4. If you want to switch the model, you might need to pass an environment variable or modify the code (depending on how model is configured, e.g., an env var `MODEL_NAME=gpt-3.5-turbo` which the code uses).

## After Execution (Retrieving Output)

Once the container finishes, it will exit (thanks to `--rm` it will be removed). The output will remain on your host in the `/path/to/output` directory you mounted.

Expected output artifacts:
- **`management_extraction.csv`** (or similarly named file): This CSV will contain the extracted names and roles. Each row typically has the source identifier (e.g. company or file name), the name of the person, and their role.
- There might also be a log or report, depending on implementation (for example, the script could write a summary log file). Check the output directory for any additional files.
- If JSON output is chosen instead of CSV, you might see an `output.json` containing an array of results or individual JSON files per input. (By default, we expect a single CSV for simplicity.)

Open the CSV to verify contents. It should look something like:

```
source,name,role
Example Mining Corp,John Doe,Chief Executive Officer
Example Mining Corp,Jane Smith,Chief Financial Officer
Another Mining Ltd,Alan Johnson,VP of Operations
...
```

Where *source* is either the company name or file identifier (depending on how the pipeline writes it, but it will correspond to the input origin).

## Running Locally (Without Docker, Optional)

If for some reason you prefer running the pipeline directly on your host (not in Docker), you would need to:
- Install Python and the required libraries (`pip install -r requirements.txt`).
- Set the `OPENAI_API_KEY` in your environment.
- Run the main script: `python src/pipeline.py --input /path/to/input_jsons --output /path/to/output`.
- This approach is less encapsulated than Docker and may encounter environment issues. Docker is recommended for consistency.

## Scaling and Performance Tips

Processing 150k files sequentially with an LLM might be very slow (could take days if each API call is ~1 second or more). To speed up:
- **Parallel Docker runs**: Split your input directory into multiple parts (e.g., 5 chunks of 30k files each in separate folders). Open 5 terminals (or create a Docker Compose file) and run 5 containers in parallel, each pointed at a different input subfolder and a different output file. Make sure to also manage separate API keys or throttle usage to avoid hitting rate limits.
- **Use GPT-3.5 for initial run**: If cost or time is a concern, you can run with `MODEL_NAME=gpt-3.5-turbo` (if the code supports a model switch via env var or config) to get results quicker, then perhaps re-run on a smaller subset with GPT-4 for verification.
- **Adjust logging**: Excessive logging for each file can slow down the process. For very large runs, you might want to only log summary info (e.g., every 100 files) instead of each file. This can be configured in the code (via logging level).

## Troubleshooting

- If the container exits immediately with no output, run `docker logs <container_id>` (if not using `--rm`) or remove `--rm` to see what happened. It could be an error like "API key not set" or a Python exception.
- Common issues:
  - *API Key missing*: Make sure you passed the `-e OPENAI_API_KEY`. The script will likely throw an error if it's not set.
  - *Network issues*: The container needs internet access to reach the OpenAI API. Ensure your network allows this. If behind a proxy, you may need to configure Docker to use it.
  - *Memory issues*: Unlikely, since the script processes one file at a time, but if you see it using a lot of memory, ensure you're not storing huge objects inadvertently. Docker by default can use swap; you might limit memory with `--memory="4g"` if needed.
  - *Output file not appearing*: Possibly a permission issue. Ensure the user in Docker has permission to write to the mounted volume. In the Dockerfile, you might add a line to run as a non-root user. Alternatively, adjust permissions on the host output folder (e.g., `chmod 777` for a quick fix in a controlled environment).

By following this usage guide, you should be able to execute the pipeline and obtain the list of management names and roles from the dataset. For any changes to the pipeline behavior or configuration, refer to the other docs (especially **PIPELINE.md** and **TECH_STACK.md**) and update the usage steps accordingly.
