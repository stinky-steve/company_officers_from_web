# DATA_FORMAT.md

This document describes the structure of the input JSON files and provides an example. Understanding the input format is crucial for parsing the data correctly and feeding it into the extraction pipeline.

## Input JSON Structure

Each JSON file corresponds to a single page of a mining company's website (often an "About Us", "Leadership", or "Team" page containing management information). While the exact structure can vary slightly depending on the scraping process, the files have a consistent set of fields. Key fields typically include:

- **company** or **company_name** (string): The name of the company. This might be derived from the website domain or the page content. (In some cases, this might not be present if the context is clear from file grouping, but we assume it's provided for clarity.)
- **url** (string): The URL of the page from which content was scraped. This can help in troubleshooting or if additional context about the source is needed.
- **page_title** (string): The title of the webpage (for example, "Leadership Team – Example Mining Corp"). This can provide a hint about the content. Not strictly required for extraction but good for context.
- **content** or **text** (string): The main textual content of the page. This is the field the pipeline uses for extraction. It usually contains the names of people and their roles among other text on the page.
- **scrape_date** (string or timestamp): *(Optional)* The date when the page was scraped. Not used in extraction, but included for record-keeping.

Additional fields might be present depending on the scraping tool (for example, an **id** or **metadata** field, or an **html** field containing raw HTML). However, the **content/text** field is the primary input for the LLM. If an **html** field exists but no cleaned text, the pipeline's preprocessing step will convert HTML to text.

**Important:** The content field may include newlines, bullet points, or other formatting artifacts as they appeared on the website. The extraction prompt is designed to handle these, but extremely non-standard formatting might need pre-cleaning.

## Example JSON File

Here is a simplified example of a JSON file (`example_company_leadership.json`) to illustrate the format:

```json
{
  "company_name": "Example Mining Corp",
  "url": "https://www.examplemining.com/about/leadership",
  "page_title": "Leadership Team - Example Mining Corp",
  "content": "Our Leadership Team\\n\\nJohn Doe - Chief Executive Officer\\nJane Smith – Chief Financial Officer\\nAlan Johnson, VP of Operations\\nMary Brown – Director of Exploration\\n\\nExample Mining Corp is committed to ...",
  "scrape_date": "2025-03-01"
}
```

**Explanation:**

- `company_name`: Name of the company (Example Mining Corp).
- `url`: Direct link to the leadership team page.
- `page_title`: The title of the page (often contains "Leadership Team" indicating relevant content).
- `content`: The text extracted from the page. In this example, the content includes a header "Our Leadership Team" followed by names and roles:
  - **John Doe - Chief Executive Officer**  
  - **Jane Smith – Chief Financial Officer**  
  - **Alan Johnson, VP of Operations**  
  - **Mary Brown – Director of Exploration**  
  (Each entry is separated by a newline `\\n`. Note the use of both hyphen `-` and en-dash `–` as separators in the example, and a comma in one of the titles. The LLM is capable of interpreting these formats.)
- `scrape_date`: The date when this data was fetched. This field is not used in processing, but retained for reference.

In practice, actual files might not have the exact same keys; for example, some may use `"text"` instead of `"content"`. The pipeline code is written to handle such minor variations (by checking alternate keys). Consistency in the input format will simplify the pipeline, so it's recommended to normalize the JSON structure if possible before running extraction (e.g., ensure all files use `"content"` as the key for page text).

## Handling of HTML Content

If the JSON files contain raw HTML (e.g., a field `"html": "<div>...</div>"`), the pipeline's preprocessing will convert it to plain text. This typically involves:
- Stripping out HTML tags.
- Replacing HTML entities with their character equivalents.
- Preserving meaningful separators (like paragraphs or list breaks) as newlines in the text.

The example above shows a clean text content. If your data is not pre-cleaned, you may need to incorporate an HTML-to-text step. This can be done with libraries like **BeautifulSoup4** in Python to parse and extract text from HTML.

## Data Volume and Organization

Given ~150,000 JSON files, they might be organized in subdirectories (for instance, grouped by company or source). The pipeline can be pointed at the top-level directory and it will traverse all subdirectories to find JSON files. It's important that the JSON structure is uniform enough that one parsing logic works for all.

Each file ideally contains one page's content. If a company's leadership is split across multiple pages (less common, but e.g., separate pages for Board of Directors vs Executive Team), those would be separate JSON files and the pipeline will process each. The output will later be combined per company if needed (since the output includes company name or another identifier, one can group results after extraction).

In summary, ensure the JSON files have a clear content field with the text to analyze. The example provided can be used as a template to verify that your data looks correct before running the pipeline. Misformatted JSON or unexpected field names are a common source of errors, so double-checking a few samples against this specification is recommended. 