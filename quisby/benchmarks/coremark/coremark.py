from itertools import groupby
import re
from quisby import custom_logger
from quisby.util import read_config, process_instance, mk_int
from quisby.pricing.cloud_pricing import get_cloud_pricing


# Utility function to extract prefix, number, and suffix from instance names
def extract_prefix_and_number(input_string):
    """
    Extracts the prefix, number, and suffix from a structured instance name string.

    Example: 't2.micro-01' -> ('t2.micro', 1, '')

    :param input_string: The instance name as a string (e.g., 't2.micro-01')
    :return: Tuple (prefix, number, suffix) or (None, None, None) if no match
    """
    try:
        match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
        if match:
            prefix = match.group(1)
            number = int(match.group(2))
            suffix = match.group(3)
            return prefix, number, suffix
    except Exception as exc:
        custom_logger.error(f"Error extracting prefix and number from input string '{input_string}': {str(exc)}")
    return None, None, None


# Custom key for sorting instances based on the cloud type and instance name
def custom_key(item):
    """
    Generates a custom sorting key based on the instance's cloud platform (AWS, GCP, Azure, or Local).

    :param item: The item containing instance name
    :return: Tuple that can be used as a sorting key
    """
    try:
        cloud_type = read_config("cloud", "cloud_type")

        if item[1][0] == "local":
            return item[1][0]  # If local, use the first item directly as the key

        # For cloud instances, split names to extract type and number
        if cloud_type == "aws":
            instance_name = item[1][0]
            instance_type, instance_number = instance_name.split(".")
            return instance_type, instance_number

        elif cloud_type == "gcp":
            instance_type = item[1][0].split("-")[0]
            instance_number = int(item[1][0].split('-')[-1])
            return instance_type, instance_number

        elif cloud_type == "azure":
            instance_type, version, instance_number = extract_prefix_and_number(item[1][0])
            return instance_type, version, instance_number

    except Exception as exc:
        custom_logger.error(f"Error generating custom key for instance '{item[1][0]}': {str(exc)}")
    return None


# Calculates price-performance ratio for an instance
def calc_price_performance(inst, avg):
    """
    Calculates the price-performance ratio for a given instance.

    :param inst: Instance identifier (e.g., 't2.micro')
    :param avg: Average performance for the instance
    :return: Tuple (cost per hour, price-performance ratio)
    """
    try:
        region = read_config("cloud", "region")
        cloud_type = read_config("cloud", "cloud_type")
        os_type = read_config("test", "os_type")

        cost_per_hour = get_cloud_pricing(inst, region, cloud_type.lower(), os_type)
        price_perf = float(avg) / float(cost_per_hour)

        return cost_per_hour, price_perf

    except Exception as exc:
        custom_logger.error(f"Error calculating price-performance for instance '{inst}': {str(exc)}")
        return None, 0.0


# Groups benchmarking results based on cloud platform
def group_data(results):
    """
    Groups benchmarking results based on instance type and cloud platform.

    :param results: List of benchmarking results
    :return: Grouped results
    """
    try:
        cloud_type = read_config("cloud", "cloud_type")

        if cloud_type == "aws":
            return groupby(results, key=lambda x: process_instance(x[1][0], "family", "version", "feature", "machine_type"))

        elif cloud_type == "azure":
            results = sorted(results, key=lambda x: process_instance(x[1][0], "family", "feature"))
            return groupby(results, key=lambda x: process_instance(x[1][0], "family", "feature"))

        elif cloud_type == "gcp":
            return groupby(results, key=lambda x: process_instance(x[1][0], "family", "version", "sub_family", "feature"))

        elif cloud_type == "local":
            return groupby(results, key=lambda x: process_instance(x[1][0], "family"))
    except Exception as exc:
        custom_logger.error(f"Error grouping benchmarking results: {str(exc)}")
    return []


# Sorts the results based on cloud platform naming conventions
def sort_data(results):
    """
    Sorts the benchmarking results based on instance naming conventions.

    :param results: List of benchmarking results
    """
    try:
        cloud_type = read_config("cloud", "cloud_type")

        if cloud_type == "aws":
            results.sort(key=lambda x: str(process_instance(x[1][0], "family")))

        elif cloud_type == "azure":
            results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "feature")))

        elif cloud_type == "gcp":
            results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "sub_family")))

    except Exception as exc:
        custom_logger.error(f"Error sorting benchmarking results: {str(exc)}")


# Generates a summary report for CoreMark benchmarking data
def create_summary_coremark_data(results, OS_RELEASE, sorted_results=None):
    """
    Generates a summary report for CoreMark data including average performance, cost per hour, and price-performance.

    :param results: Benchmarking results
    :param OS_RELEASE: OS release string (e.g., 'Ubuntu-20.04')
    :param sorted_results: Pre-sorted benchmarking data (optional)
    :return: Final report in structured format
    """
    final_results = []

    try:
        # Sort and filter results
        results = list(filter(None, results))
        sort_data(results)

        for _, items in group_data(results):
            cal_data = [["System name", "Test_passes-" + OS_RELEASE]]
            items = list(items)
            sorted_data = sorted(items, key=lambda x: mk_int(process_instance(x[1][0], "size")))

            cost_per_hour, price_per_perf = [], []

            # Add summary data for each instance
            for item in sorted_data:
                sum = 0
                avg = 0
                iterations = 0

                # Calculate average performance
                for index in range(3, len(item)):
                    sum += float(item[index][1])
                    iterations += 1
                avg = float(sum / iterations)

                # Calculate cost per hour and price-perf
                try:
                    cph, pp = calc_price_performance(item[1][0], avg)
                except Exception as exc:
                    custom_logger.error(f"Error calculating price-performance for instance '{item[1][0]}': {str(exc)}")
                    break

                # Add data to final report
                cal_data.append([item[1][0], avg])
                price_per_perf.append([item[1][0], pp])
                cost_per_hour.append([item[1][0], cph])

            # Compile the summary report
            sorted_results = [[""]]
            sorted_results += cal_data
            sorted_results.append([""])
            sorted_results.append(["Cost/Hr"])
            sorted_results += cost_per_hour
            sorted_results.append([""])
            sorted_results.append(["Price-perf", f"Passes/$-{OS_RELEASE}"])
            sorted_results += price_per_perf

            final_results.extend(sorted_results)

    except Exception as exc:
        custom_logger.error(f"Error creating CoreMark summary data: {str(exc)}")

    return final_results


# Extracts and processes CoreMark data from a file
def extract_coremark_data(path, system_name, OS_RELEASE):
    """
    Extracts and processes CoreMark results from a file (CSV format).

    :param path: Path to the file containing benchmarking results
    :param system_name: The name of the system being benchmarked
    :param OS_RELEASE: OS release version (e.g., 'Ubuntu-20.04')
    :return: Processed benchmarking results or None if there was an error
    """
    results = []
    processed_data = []

    try:
        # Open the CSV file
        if path.endswith(".csv"):
            with open(path) as file:
                coremark_results = file.readlines()
        else:
            custom_logger.error(f"Invalid file format for path: {path}")
            return None  # Not a CSV file
    except Exception as exc:
        custom_logger.error(f"Error reading CSV file '{path}': {str(exc)}")
        return None  # Error reading file

    # Process the CoreMark data
    try:
        data_index = 0
        header = []
        for index, data in enumerate(coremark_results):
            if "iteration" in data:
                data_index = index
                header = data.strip("\n").split(":")
            else:
                coremark_results[index] = data.strip("\n").split(":")
        coremark_results = [header] + coremark_results[data_index + 1:]

        # Format the data for report generation
        iteration = 1
        for row in coremark_results:
            if "test passes" in row:
                processed_data.append([""])
                processed_data.append([system_name])
                processed_data.append([row[0], row[2]])  # System name and test passes
            else:
                processed_data.append([iteration, row[2]])  # Iteration and performance
                iteration += 1

        results.append(processed_data)
    except Exception as exc:
        custom_logger.error(f"Error processing CoreMark data from file '{path}': {str(exc)}")
        return None

    return results
