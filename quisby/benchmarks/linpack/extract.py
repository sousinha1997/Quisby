import csv
import glob
import logging
import os
import re
from quisby.pricing.cloud_pricing import get_cloud_pricing, get_cloud_cpu_count
from quisby.util import read_config

# Setting up logger for better error tracking and debugging
logger = logging.getLogger(__name__)


def linpack_format_data(**kwargs):
    """
    Adds data into a format suitable for spreadsheets.

    This function processes Linpack-like data (e.g., autohpl) to include system
    information, GFLOPS, pricing, and CPU cores.

    Args:
        kwargs: A dictionary containing the required input data, including:
            - 'results': List to store formatted data.
            - 'system_name': The name of the system being tested.
            - 'gflops': The GFLOPS result from the test.

    Returns:
        list: Updated 'results' list with the new data.
        None: If GFLOPS data is not available or invalid.
    """
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type").lower()
    os_release = read_config("test", "OS_RELEASE")
    os_type = read_config("test", "os_type")

    results = kwargs.get("results", [])
    system_name = kwargs.get("system_name")

    # Ensure GFLOPS is provided and valid
    gflops = kwargs.get("gflops")
    if not gflops:
        logger.warning(f"GFLOPS value is missing for system {system_name}. Skipping.")
        return None

    try:
        gflops = float(gflops)
    except ValueError:
        logger.error(f"Invalid GFLOPS value: {gflops}. Could not convert to float.")
        raise ValueError(f"Invalid GFLOPS value: {gflops}. Could not convert to float.")

    # Fetch pricing and CPU details from the cloud pricing API
    try:
        price_per_hour = get_cloud_pricing(system_name, region, cloud_type, os_type)
        no_of_cores = get_cloud_cpu_count(system_name, region, cloud_type)
    except Exception as e:
        logger.error(f"Error fetching cloud pricing or CPU count for system {system_name}: {str(e)}")
        raise RuntimeError(f"Error fetching cloud pricing or CPU count: {str(e)}")

    # If price_per_hour is invalid or 0, return an empty result to avoid divide by zero errors
    if not price_per_hour or price_per_hour == 0.0:
        logger.warning(f"Invalid price_per_hour for system {system_name}, skipping.")
        return []

    # Append formatted data to results
    results.append([
        system_name,
        no_of_cores,
        gflops,
        1,  # Assuming '1' refers to a single test instance
        price_per_hour,
        gflops / price_per_hour
    ])

    return results


def extract_linpack_data(path, system_name):
    """
    Extracts Linpack summary data from files and formats it for analysis.

    This function handles the extraction of data from Linpack summary files
    and provides information about GFLOPS and the number of cores used.

    Args:
        path (str): Path to the directory containing Linpack summary files.
        system_name (str): Name of the system being tested.

    Returns:
        tuple: A tuple containing:
            - list: Processed Linpack results.
            - list: Summary data including file paths for reference.
    """
    results = []
    summary_data = []
    no_of_cores = None
    gflops = None

    # Check if the summary file exists
    summary_file = path
    if not os.path.isfile(summary_file):
        logger.error(f"Summary file {summary_file} not found for system {system_name}.")
        raise FileNotFoundError(f"Summary file {summary_file} not found.")

    # Process CSV summary file
    if summary_file.endswith("csv"):
        try:
            with open(summary_file, 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=":")
                list_data = list(csv_reader)
                last_row = list_data[-1]

                gflops = last_row.get("MB/sec")
                threads = last_row.get("threads")
        except Exception as e:
            logger.error(f"Error reading CSV summary file {summary_file}: {str(e)}")
            raise RuntimeError(f"Error reading CSV summary file {summary_file}: {str(e)}")
    else:
        # Return empty results if the file is not CSV
        logger.warning(f"Summary file {summary_file} is not in CSV format. Skipping.")
        return results

    # Process individual Linpack result files
    if threads:
        for file_path in glob.glob(f"{path}/linpack*_threads_{threads}_*"):
            try:
                with open(file_path, 'r') as txt_file:
                    data = txt_file.readlines()
                    for row in data:
                        match = re.search(r"Number of cores: (\d+)", row)
                        if match:
                            no_of_cores = match.group(1)
                            break
            except Exception as e:
                logger.error(f"Error reading Linpack result file {file_path}: {str(e)}")
                raise RuntimeError(f"Error reading Linpack result file {file_path}: {str(e)}")

    # If GFLOPS data is found, format and append it
    if gflops:
        results = linpack_format_data(
            results=results,
            system_name=system_name,
            no_of_cores=no_of_cores,
            gflops=gflops
        )

    return results
