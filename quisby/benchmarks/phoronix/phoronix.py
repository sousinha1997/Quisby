from itertools import groupby
from scipy.stats import gmean
from quisby import custom_logger
from quisby.util import read_config
from quisby.pricing.cloud_pricing import get_cloud_pricing
import re
from quisby.util import process_instance, mk_int


def extract_prefix_and_number(input_string):
    """
    Extracts the prefix, number, and suffix from an input string.

    Args:
        input_string (str): The string to extract from.

    Returns:
        tuple: A tuple containing the prefix, the number, and the suffix.
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
    Creates a custom sorting key based on the cloud provider type.

    Args:
        item (tuple): A tuple containing instance data.

    Returns:
        tuple: The sorting key based on instance data.
    """
    cloud_type = read_config("cloud", "cloud_type")
    if item[0] == "local":
        return item[0]
    elif cloud_type == "aws":
        instance_type = item[0].split(".")[0]
        instance_number = item[0].split(".")[1]
        return instance_type, instance_number
    elif cloud_type == "gcp":
        instance_type = item[0].split("-")[0]
        instance_number = int(item[0].split('-')[-1])
        return instance_type, instance_number
    elif cloud_type == "azure":
        instance_type, instance_number, version = extract_prefix_and_number(item[0])
        return instance_type, version, instance_number


def calc_price_performance(inst, avg):
    """
    Calculates the price performance of an instance.

    Args:
        inst (str): The instance identifier.
        avg (float): The average performance data.

    Returns:
        tuple: The cost per hour and price performance of the instance.
    """
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")
    cost_per_hour = None
    try:
        cost_per_hour = get_cloud_pricing(inst, region, cloud_type.lower(), os_type)
        price_perf = float(avg) / float(cost_per_hour)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Error calculating value!")
    return cost_per_hour, price_perf


def group_data(results):
    """
    Groups the data based on the cloud provider type.

    Args:
        results (list): A list of instance data.

    Returns:
        groupby: A grouped object containing instance data based on cloud provider type.
    """
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "aws":
        return groupby(results, key=lambda x: process_instance(x[1][0], "family", "version", "feature", "machine_type"))
    elif cloud_type == "azure":
        results = sorted(results, key=lambda x: process_instance(x[1][0], "family", "feature"))
        return groupby(results, key=lambda x: process_instance(x[1][0], "family", "version", "feature"))
    elif cloud_type == "gcp":
        return groupby(results, key=lambda x: process_instance(x[1][0], "family", "version", "sub_family", "feature"))
    elif cloud_type == "local":
        return groupby(results, key=lambda x: process_instance(x[1][0], "family"))


def sort_data(results):
    """
    Sorts the data based on the cloud provider type.

    Args:
        results (list): A list of instance data.
    """
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "aws":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family")))
    elif cloud_type == "azure":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "feature")))
    elif cloud_type == "gcp":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "sub_family")))


def create_summary_phoronix_data(data, OS_RELEASE):
    """
    Creates a summary of Phoronix benchmark data with price/performance and geomean.

    Args:
        data (list): The data to summarize.
        OS_RELEASE (str): The operating system release.

    Returns:
        list: A list containing the summary data.
    """
    ret_results = []

    # Filter out empty results
    results = list(filter(None, data))
    sort_data(results)
    results = group_data(results)

    # Loop through each group and calculate the necessary values
    for _, items in results:
        mac_data = [["System name", "Geomean-" + OS_RELEASE]]
        cost_data = [["Cost/Hr"]]
        price_perf_data = [["Price-perf", f"Geomean/$-{OS_RELEASE}"]]

        items = list(items)
        sorted_data = sorted(items, key=lambda x: mk_int(process_instance(x[1][0], "size")))
        cost_per_hour, price_per_perf = [], []

        # Add summary data for each instance
        for index, row in enumerate(sorted_data):
            inst = row[1][0]
            gmean_data = []
            for i in range(2, len(row)):
                try:
                    gmean_data.append(float(row[i][1].strip()))
                except Exception as exc:
                    gmean_data.append(0.0)
            gdata = gmean(gmean_data)

            try:
                cph, pp = calc_price_performance(inst, gdata)
            except Exception as exc:
                custom_logger.error(str(exc))
                continue

            # Append the calculated values to the results
            mac_data.append([inst, gdata])
            cost_data.append([inst, cph])
            price_perf_data.append([inst, pp])

        # Add the grouped data to the final results
        ret_results.append([""])
        ret_results.extend(mac_data)
        ret_results.append([""])
        ret_results.extend(cost_data)
        ret_results.append([""])
        ret_results.extend(price_perf_data)

    return ret_results


def extract_phoronix_data(path, system_name, OS_RELEASE):
    """
    Extracts Phoronix benchmark data from a file and formats it for further processing.

    Args:
        path (str): The path to the results file.
        system_name (str): The system name associated with the results.
        OS_RELEASE (str): The operating system release.

    Returns:
        list: A list containing the extracted data.
    """
    results = []

    # Extract data from file
    try:
        if path.endswith("results.csv"):
            with open(path) as file:
                phoronix_results = file.readlines()
        else:
            return None
    except Exception as exc:
        custom_logger.error(str(exc))
        return None

    # Extract header and data
    data_index = 0
    header = []
    for index, data in enumerate(phoronix_results):
        if "Test:BOPs" in data:
            data_index = index
            header = data.strip("\n").split(":")
        else:
            phoronix_results[index] = data.strip("\n").split(":")

    # Combine header and data, and append the system name
    phoronix_results = [header] + phoronix_results[data_index + 1:]
    results.append([""])
    results.append([system_name])
    results.extend(phoronix_results[1:])

    return [results]
