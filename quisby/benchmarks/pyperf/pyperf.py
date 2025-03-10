from itertools import groupby
from scipy.stats import gmean
from quisby import custom_logger
from quisby.util import read_config
from quisby.pricing.cloud_pricing import get_cloud_pricing
import re
from quisby.util import process_instance, mk_int


def extract_prefix_and_number(input_string):
    """
    Extracts the prefix, numeric part, and suffix from a string.

    Args:
        input_string (str): The input string containing the prefix, number, and suffix.

    Returns:
        tuple: A tuple containing the prefix, number, and suffix. If the pattern isn't matched, returns None values.
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
    Custom sorting key function based on cloud type and instance details.

    Args:
        item (tuple): Tuple where the first element is the instance identifier.

    Returns:
        tuple: A tuple representing the instance sorting key.
    """
    cloud_type = read_config("cloud", "cloud_type")
    if item[0] == "local":
        return item[0]
    elif cloud_type == "aws":
        instance_type, instance_number = item[0].split(".")
        return instance_type, instance_number
    elif cloud_type == "gcp":
        instance_type, instance_number = item[0].split('-')[0], int(item[0].split('-')[-1])
        return instance_type, instance_number
    elif cloud_type == "azure":
        instance_type, version, instance_number = extract_prefix_and_number(item[0])
        return instance_type, version, instance_number


def calc_price_performance(inst, avg):
    """
    Calculates the price-performance ratio for a given instance.

    Args:
        inst (str): Instance identifier.
        avg (float): Average performance value.

    Returns:
        tuple: Cost per hour and price-performance ratio.
    """
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")
    cost_per_hour = None
    price_perf = 0.0
    try:
        cost_per_hour = get_cloud_pricing(inst, region, cloud_type.lower(), os_type)
        price_perf = float(avg) / float(cost_per_hour)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Error calculating value!")
    return cost_per_hour, price_perf


def group_data(results):
    """
    Groups the data based on cloud type and instance characteristics.

    Args:
        results (list): List of result items.

    Returns:
        groupby object: Grouped data based on cloud type and instance characteristics.
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
    Sorts the results data based on cloud type.

    Args:
        results (list): List of result items to be sorted.
    """
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "aws":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family")))
    elif cloud_type == "azure":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "feature")))
    elif cloud_type == "gcp":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "sub_family")))


def create_summary_pyperf_data(data, OS_RELEASE):
    """
    Creates a summary of performance data for a given OS release.

    Args:
        data (list): List of performance data.
        OS_RELEASE (str): The OS release to associate with the data.

    Returns:
        list: Summary results including the system name, geomean values, cost per hour, and price performance.
    """
    ret_results = []

    results = list(filter(None, data))
    sort_data(results)
    results = group_data(results)
    for _, items in results:
        mac_data = [["System name", "Geomean-" + OS_RELEASE]]
        cost_data = [["Cost/Hr"]]
        price_perf_data = [["Price-perf", f"Geomean/$-{OS_RELEASE}"]]
        items = list(items)
        sorted_data = sorted(items, key=lambda x: mk_int(process_instance(x[1][0], "size")))
        cost_per_hour, price_per_perf = [], []

        # Add summary data
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

            mac_data.append([inst, gdata])
            cost_data.append([inst, cph])
            price_perf_data.append([inst, pp])

        ret_results.append([""])
        ret_results.extend(mac_data)
        ret_results.append([""])
        ret_results.extend(cost_data)
        ret_results.append([""])
        ret_results.extend(price_perf_data)

    return ret_results


def extract_pyperf_data(path, system_name, OS_RELEASE):
    """
    Extracts and processes pyperf data from a given file.

    Args:
        path (str): Path to the pyperf data file.
        system_name (str): The system name to associate with the data.
        OS_RELEASE (str): The OS release to associate with the data.

    Returns:
        list: Extracted results in a structured format.
    """
    results = []

    # Extract data from file
    try:
        if path:
            with open(path) as file:
                pyperf_results = file.readlines()
        else:
            return None
    except Exception as exc:
        custom_logger.error(str(exc))
        return None

    # Process the pyperf data
    data_index = 0
    for index, data in enumerate(pyperf_results):
        if "Test:Avg:Unit" in data:
            data_index = index
            header = data.strip("\n").split(":")
        else:
            pyperf_results[index] = data.strip("\n").split(":")

    pyperf_results = [header] + pyperf_results[data_index + 1:]
    results.append([""])
    results.append([system_name])
    results.extend(pyperf_results[1:])
    return [results]
