"""Script to test the DataReader functionality with MinIO data."""

import json
from pathlib import Path
from typing import List, Tuple
from tqdm import tqdm
import logging

from src.services.minio_service import MinioService
from src.data_reader import DataReader
from src.config import settings

# Configure logging to output to both console and a log file.
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "test_data_reader.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, mode="w", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Optionally set logging to DEBUG during development:
logging.getLogger().setLevel(logging.DEBUG)

# Constants
MINIO_BUCKET = "min-co-web-page-data"
ANALYSIS_OUTPUT_FILE = Path("data/analysis_output.txt")


def is_excluded_url(url: str) -> bool:
    """Return True if the URL contains any excluded keyword."""
    excluded_keywords = ["press-release", "news", "blog", "announcement", "news-room", "press-releases", "projects"]
    return any(kw in url.lower() for kw in excluded_keywords)


def get_company_files(minio_service: MinioService, company_domain: str) -> List[str]:
    """Get all files for a specific company domain, excluding URLs with unwanted keywords."""
    all_files = minio_service.list_objects()
    return [f for f in all_files if company_domain in f and not is_excluded_url(f)]


def save_sample_content(content: str, index: int):
    """Save sample content for manual inspection."""
    output_dir = Path("data/test_samples")
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_file = output_dir / f"sample_{index}_summary.txt"
    sample_file.write_text(content, encoding="utf-8")


def process_company_files(
    data_reader: DataReader, company_domain: str, company_name: str
) -> Tuple[int, int, List]:
    """Process all files for a specific company.

    Returns:
        processed_files: Number of files that yielded people.
        total_people: Total number of people extracted.
        company_people: List of all Person objects extracted.
    """
    logger.info(f"Processing files for {company_name} ({company_domain})")
    files = get_company_files(data_reader.minio_service, company_domain)
    logger.info(f"Found {len(files)} files to process")

    processed_files = 0
    total_people = 0
    company_people = []

    for i, file in enumerate(tqdm(files, desc="Processing files"), 1):
        try:
            content = data_reader.read_json_file(file)
            if not content:
                continue

            processed_content = data_reader.process_content(content)
            if not processed_content:
                continue

            # Save sample content for manual review.
            save_sample_content(str(processed_content), i)

            exec_count = len(processed_content.executives)
            board_count = len(processed_content.board_members)
            people_count = exec_count + board_count

            if people_count > 0:
                total_people += people_count
                processed_files += 1
                company_people.extend(processed_content.executives)
                company_people.extend(processed_content.board_members)

                logger.info(f"\nFile {i}:")
                logger.info(f"URL: {processed_content.url}")
                logger.info(f"Title: {processed_content.title}")
                logger.info(f"Executives found: {exec_count}")
                logger.info(f"Board members found: {board_count}")
                if exec_count:
                    logger.info("Executives/Officers:")
                    for person in processed_content.executives:
                        logger.info(f"- {person.name} ({person.role})")
                        if person.contact_info:
                            logger.info(f"  Contact: {person.contact_info}")
                if board_count:
                    logger.info("Board Members:")
                    for person in processed_content.board_members:
                        logger.info(f"- {person.name} ({person.role})")
                        if person.contact_info:
                            logger.info(f"  Contact: {person.contact_info}")
        except Exception as e:
            logger.error(f"Error processing file {file}: {str(e)}")
            continue

    return processed_files, total_people, company_people


def write_analysis_output(
    company_name: str,
    company_domain: str,
    processed_files: int,
    total_people: int,
    company_people: List
):
    """Write the final analysis summary to a file, including JSON output for final lists."""
    output_lines = [
        "Processing Summary",
        "=" * 50,
        f"Company: {company_name}",
        f"Domain: {company_domain}",
        f"Files processed: {processed_files}",
        f"Total people found: {total_people}",
        ""
    ]

    if company_people:
        # Create separate unique lists for executives and board members.
        unique_exec = list({p.name: p for p in company_people if p.role in DataReader.EXECUTIVE_ROLES}.values())
        unique_board = list({p.name: p for p in company_people if p.role in DataReader.BOARD_ROLES}.values())

        output_lines.append("=== Unique Executives/Officers ===")
        output_lines.append("-" * 50)
        for person in unique_exec:
            output_lines.append(f"\nName: {person.name}")
            output_lines.append(f"Role: {person.role}")
            if person.contact_info:
                output_lines.append("Contact Info:")
                for key, value in person.contact_info.items():
                    output_lines.append(f"  {key}: {value}")

        output_lines.append("\n=== Unique Board Members ===")
        output_lines.append("-" * 50)
        for person in unique_board:
            output_lines.append(f"\nName: {person.name}")
            output_lines.append(f"Role: {person.role}")
            if person.contact_info:
                output_lines.append("Contact Info:")
                for key, value in person.contact_info.items():
                    output_lines.append(f"  {key}: {value}")

        # Append final JSON output for executives.
        output_lines.append("\n\n=== Final Executives List (JSON) ===")
        exec_json = json.dumps(
            [{"name": p.name, "role": p.role, "contact_info": p.contact_info} for p in unique_exec],
            indent=2
        )
        output_lines.append(exec_json)

        # Append final JSON output for board members.
        output_lines.append("\n\n=== Final Board Members List (JSON) ===")
        board_json = json.dumps(
            [{"name": p.name, "role": p.role, "contact_info": p.contact_info} for p in unique_board],
            indent=2
        )
        output_lines.append(board_json)
    else:
        output_lines.append("No people found.")

    analysis_output = "\n".join(output_lines)
    ANALYSIS_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    ANALYSIS_OUTPUT_FILE.write_text(analysis_output, encoding="utf-8")
    logger.info(f"Analysis output saved to {ANALYSIS_OUTPUT_FILE}")


def main():
    """Test the DataReader with a sample company."""
    try:
        logger.info("Creating DataReader instance...")
        minio_service = MinioService()
        data_reader = DataReader(minio_service, MINIO_BUCKET)

        # Specify the company to process.
        company_domain = "ayagoldsilver.com"
        company_name = "Aya Gold & Silver Inc."

        processed_files, total_people, company_people = process_company_files(
            data_reader, company_domain, company_name
        )

        # Print summary to console.
        summary = (
            f"\nProcessing Summary\n{'=' * 50}\n"
            f"Company: {company_name}\n"
            f"Domain: {company_domain}\n"
            f"Files processed: {processed_files}\n"
            f"Total people found: {total_people}\n"
        )
        print(summary)
        if company_people:
            print("Unique People Found (Combined List)")
            print("-" * 50)
            unique_people = {p.name: p for p in company_people}.values()
            for person in unique_people:
                print(f"\nName: {person.name}")
                print(f"Role: {person.role}")
                if person.contact_info:
                    print("Contact Info:")
                    for key, value in person.contact_info.items():
                        print(f"  {key}: {value}")

        # Save the summary analysis to a file.
        write_analysis_output(company_name, company_domain, processed_files, total_people, company_people)

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main()
