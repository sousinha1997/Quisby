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

        if not file_data:
            raise ValueError("Empty File")

        # Check for minimum required data
        if len(file_data) < 2:
            logger.warning(f"Insufficient data in file: {path}")
            return None

        data_row = None
        data_index = 0
        header_row = []
        for index, data in enumerate(file_data):
            if "Gflops" in data:
                data_index = index
                header_row = data.strip("\n").split(":")

        if not header_row:
            raise KeyError("Missing 'Gflops' in data")

        if len(file_data) > data_index+1:
            data_row = file_data[data_index+1].strip().split(":")

        # Check if insufficient data
        if not data_row:
            return None

        # Validate data extraction
        if len(header_row) != len(data_row):
            raise ValueError("Mismatched header and data lengths")

        # Create dictionary from rows
        data_dict = dict(zip(header_row, data_row))

        # Process and format data
        results: List[Dict[str, str]] = []
        formatted_results = linpack_format_data(
            results=results,
            system_name=system_name,
            gflops=data_dict["Gflops"]
        )

        return formatted_results if formatted_results else None
