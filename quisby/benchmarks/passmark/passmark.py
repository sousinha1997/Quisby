import re
from itertools import groupby
from scipy.stats import gmean
from quisby import custom_logger
from quisby.util import read_config
from quisby.pricing.cloud_pricing import get_cloud_pricing
from quisby.util import process_instance, mk_int


def extract_prefix_and_number(input_string):
    """
    Extract the prefix, number, and suffix from an instance name.
    Example: 't2.micro-01' -> ('t2', 1, '.micro')

    :param input_string: Instance name string (e.g., 't2.micro-01').
    :return: Tuple (prefix, number, suffix) or (None, None, None) if no match.
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
    Generate a custom key for sorting/grouping based on the cloud provider type.

    :param item: A tuple containing instance data.
    :return: A tuple key for grouping/sorting.
    """
    cloud_type = read_config("cloud", "cloud_type")
    try:
        if item[0] == "local":
            return item[0]
        elif cloud_type == "aws":
            instance_type, instance_number = item[0].split(".")
            return instance_type, instance_number
        elif cloud_type == "gcp":
            instance_type, instance_number = item[0].split("-")
            return instance_type, int(instance_number)
        elif cloud_type == "azure":
            instance_type, version, instance_number = extract_prefix_and_number(item[0])
            return instance_type, version, instance_number
    except Exception as exc:
        custom_logger.error(f"Error in custom_key for {item[0]}: {str(exc)}")
        return "", ""


def calc_price_performance(inst, avg):
    """
    Calculate the price-performance ratio for a given instance.

    :param inst: Instance type or ID.
    :param avg: Average performance score (e.g., geometric mean).
    :return: Tuple (cost_per_hour, price_performance).
    """
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")
    cost_per_hour = None
    try:
        cost_per_hour = get_cloud_pricing(inst, region, cloud_type.lower(), os_type)
        price_perf = float(avg) / float(cost_per_hour) if cost_per_hour else 0
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Error calculating price-performance!")
    return cost_per_hour, price_perf


def group_data(results):
    """
    Group benchmark data based on cloud type and instance characteristics.

    :param results: List of benchmark results.
    :return: Grouped results.
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
    Sort benchmark data based on instance attributes and cloud type.

    :param results: List of benchmark results.
    """
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "aws":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family")))
    elif cloud_type == "azure":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "feature")))
    elif cloud_type == "gcp":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "sub_family")))


def create_summary_passmark_data(data, OS_RELEASE):
    """
    Create a summary of PassMark data, including geometric mean and price-performance metrics.

    :param data: List of benchmark data.
    :param OS_RELEASE: OS release version (e.g., "Ubuntu 20.04").
    :return: List of summarized results.
    """
    ret_results = []
    results = list(filter(None, data))
    sort_data(results)
    results = group_data(results)

    for _, items in results:
        mac_data = [["System name", f"Geomean-{OS_RELEASE}"]]
        cost_data = [["Cost/Hr"]]
        price_perf_data = [["Price-perf", f"Geomean/$-{OS_RELEASE}"]]
        items = list(items)
        sorted_data = sorted(items, key=lambda x: mk_int(process_instance(x[1][0], "size")))

        cost_per_hour, price_perf = [], []
        # Add summary data
        for index, row in enumerate(sorted_data):
            inst = row[1][0]
            gmean_data = []
            for i in range(2, len(row)):
                try:
                    gmean_data.append(float(row[i][1].strip()))
                except Exception as exc:
                    gmean_data.append(0.0)  # Default to 0.0 for non-numeric values
            gdata = gmean(gmean_data)
            try:
                cph, pp = calc_price_performance(inst, gdata)
            except Exception as exc:
                custom_logger.error(f"Error calculating price performance for {inst}: {str(exc)}")
                continue

            mac_data.append([inst, gdata])
            cost_data.append([inst, cph])
            price_perf_data.append([inst, pp])

        # Append all data for the current group
        ret_results.append([""])
        ret_results.extend(mac_data)
        ret_results.append([""])
        ret_results.extend(cost_data)
        ret_results.append([""])
        ret_results.extend(price_perf_data)

    return ret_results


def extract_passmark_data(path, system_name, OS_RELEASE):
    """
    Extract and process PassMark benchmark data from a CSV file.

    :param path: Path to the CSV file containing the benchmark results.
    :param system_name: Name of the system being tested.
    :param OS_RELEASE: OS release version (e.g., "Ubuntu 20.04").
    :return: Processed results as a list.
    """
    results = []

    # Extract data from file
    try:
        if path.endswith("results.csv"):
            with open(path) as file:
                passmark_results = file.readlines()
        else:
            return None
    except Exception as exc:
        custom_logger.error(f"Error reading file {path}: {str(exc)}")
        return None

    data_index = 0
    header = []
    for index, data in enumerate(passmark_results):
        if "NumTestProcesses:" in data:
            header = data.strip("\n").split(":")
            data_index = index
        else:
            passmark_results[index] = data.strip("\n").split(":")

    passmark_results = [header] + passmark_results[data_index + 1:]
    results.append([""])
    results.append([system_name])
    results.extend(passmark_results)
    return [results]
