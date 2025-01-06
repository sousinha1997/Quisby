import logging
from typing import List, Dict, Optional
from pathlib import Path
from quisby.benchmarks.linpack.extract import linpack_format_data


logger = logging.getLogger(__name__)


def extract_auto_hpl_data(
        path: str,
        system_name: str
) -> Optional[List[Dict[str, str]]]:
    """
    Extract Auto HPL benchmark data from a CSV file.

    Args:
        path (str): Path to the CSV file
        system_name (str): Name of the system being analyzed

    Returns:
        Optional[List[Dict[str, str]]]: Processed benchmark results or None

    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If there are insufficient permissions to read the file
        ValueError: If the file format is incorrect
    """
    # Validate input path
    file_path = Path(path)

    # Check file existence and extension
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if file_path.suffix.lower() != '.csv':
        raise ValueError(f"Invalid file type. Expected .csv, got {file_path.suffix}")


    # Read file with proper error handling
    with open(file_path, 'r', encoding='utf-8') as file:
        file_data = file.readlines()

        # Check for minimum required data
        if len(file_data) < 2:
            logger.warning(f"Insufficient data in file: {path}")
            return None


        # Extract header and data rows
        header_row = file_data[-2].strip().split(":")
        data_row = file_data[-1].strip().split(":")

        # Validate data extraction
        if len(header_row) != len(data_row):
            raise ValueError("Mismatched header and data lengths")

        # Create dictionary from rows
        data_dict = dict(zip(header_row, data_row))

        # Validate required field
        if 'Gflops' not in data_dict:
            raise KeyError("Missing 'Gflops' in data")

        # Process and format data
        results: List[Dict[str, str]] = []
        formatted_results = linpack_format_data(
            results=results,
            system_name=system_name,
            gflops=data_dict["Gflops"]
        )

        return formatted_results if formatted_results else None
