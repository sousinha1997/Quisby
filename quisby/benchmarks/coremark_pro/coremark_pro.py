import re

from quisby import custom_logger
from quisby.util import read_config


def extract_prefix_and_number(input_string):
    """
    Extract the prefix, number, and suffix from a given string.

    Args:
        input_string (str): The input string to extract from.

    Returns:
        tuple: A tuple containing the prefix (str), number (int), and suffix (str).
    """
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)
        return prefix, number, suffix
    return None, None, None


def custom_key(item):
    """
    Generate a custom sorting key based on the cloud type and instance details.

    Args:
        item (tuple): A tuple where item[1][0] represents the instance name.

    Returns:
        tuple: A tuple representing the key to be used for sorting.
    """
    cloud_type = read_config("cloud", "cloud_type")
    try:
        if item[1][0] == "localhost":
            return item[1][0]
        elif cloud_type == "aws":
            instance_type, instance_number = item[1][0].split(".")
            return instance_type, instance_number
        elif cloud_type == "gcp":
            instance_type = item[1][0].split("-")[0]
            instance_number = int(item[1][0].split('-')[-1])
            return instance_type, instance_number
        elif cloud_type == "azure":
            instance_type, instance_number, version = extract_prefix_and_number(item[1][0])
            return instance_type, instance_number
    except Exception as exc:
        custom_logger.error(f"Error in custom_key: {exc}")
        return "", ""


def create_summary_coremark_pro_data(results, os_release):
    """
    Create a summary of Coremark Pro data for multi and single iterations.

    Args:
        results (list): The results data to summarize.
        os_release (str): The operating system release version.

    Returns:
        list: A list of summarized Coremark Pro data.
    """
    final_results = []
    multi_iter = [["Multi Iterations"], ["System name", f"Score_{os_release}"]]
    single_iter = [["Single Iterations"], ["System name", f"Score_{os_release}"]]

    # Sort data based on instance name
    sorted_data = sorted(results, key=custom_key)

    # Add summary data
    for item in sorted_data:
        for index in range(3, len(item)):
            multi_iter.append([item[1][0], item[index][1]])
            single_iter.append([item[1][0], item[index][2]])

    final_results += [[""]]
    final_results += multi_iter
    final_results += [[""]]
    final_results += single_iter
    return final_results


def extract_coremark_pro_data(path, system_name, os_release):
    """
    Extract Coremark Pro data from a file and format it for summary.

    Args:
        path (str): The file path of the Coremark Pro data.
        system_name (str): The name of the system.
        os_release (str): The operating system release version.

    Returns:
        list: A list containing formatted Coremark Pro results.
    """
    results = []
    processed_data = []

    # Extract data from file
    try:
        if path.endswith(".csv"):
            with open(path) as file:
                coremark_results = file.readlines()
        else:
            return None
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Unable to extract data from CSV file for Coremark Pro")
        return None

    # Format the data
    for index, data in enumerate(coremark_results):
        coremark_results[index] = data.strip("\n").split(":")

    iteration = 1
    for row in coremark_results:
        if "Test" in row:
            processed_data.append([""])
            processed_data.append([system_name])
            processed_data.append([row[0], row[1], row[2]])
        elif "Score" in row:
            processed_data.append(["Score", row[1], row[2]])

    results.append(processed_data)
    return results
