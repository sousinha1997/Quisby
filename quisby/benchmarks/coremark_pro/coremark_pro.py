import re
from itertools import groupby

from quisby import custom_logger
from quisby.util import read_config
from quisby.pricing.cloud_pricing import get_cloud_pricing

from quisby.util import process_instance, mk_int


def extract_prefix_and_number(input_string):
    """
    Extract the prefix, number, and suffix from an instance name.

    :param input_string: Instance name like 't2.micro-01'
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
    Generate a custom key for sorting or grouping instances based on cloud provider and instance name format.

    :param item: A tuple containing instance data.
    :return: A tuple key for grouping.
    """
    cloud_type = read_config("cloud", "cloud_type")
    try:
        if item[1][0] == "local":
            return item[1][0]
        elif cloud_type == "aws":
            instance_type, instance_number = item[1][0].split(".")
            return instance_type, instance_number
        elif cloud_type == "gcp":
            instance_type, instance_number = item[1][0].split("-")
            return instance_type, int(instance_number)
        elif cloud_type == "azure":
            instance_type, version, instance_number = extract_prefix_and_number(item[1][0])
            return instance_type, version, instance_number
    except Exception as exc:
        custom_logger.error(f"Error in custom_key for {item[1][0]}: {str(exc)}")
        return "", ""


def calc_price_performance(inst, avg):
    """
    Calculate price-perf ratio for an instance based on its cost per hour and performance.

    :param inst: Instance type or ID.
    :param avg: Average score for the instance.
    :return: Tuple (cost_per_hour, price_perf)
    """
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")
    cost_per_hour = None
    price_perf = 0.0
    try:
        cost_per_hour = get_cloud_pricing(inst, region, cloud_type.lower(), os_type)
        price_perf = float(avg) / float(cost_per_hour) if cost_per_hour else 0
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Error calculating price-performance!")
    return cost_per_hour, price_perf


def group_data(results):
    """
    Group data based on cloud type and instance attributes.

    :param results: List of results to group.
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
    Sort data based on cloud type and instance attributes.

    :param results: List of results to sort.
    """
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "aws":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family")))
    elif cloud_type == "azure":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "feature")))
    elif cloud_type == "gcp":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "sub_family")))


def create_summary_coremark_pro_data(results, OS_RELEASE):
    """
    Create a summary of the CoreMark Pro data, including price-performance and iteration details.

    :param results: List of benchmark results.
    :param OS_RELEASE: OS release version (e.g., "Ubuntu 20.04").
    :return: List of summarized results.
    """
    ret_results = []

    # Sort and group data
    results = list(filter(None, results))
    sort_data(results)
    results = group_data(results)

    for _, items in results:
        multi_iter = [["Multi Iterations"], ["System name", "Score-" + OS_RELEASE]]
        single_iter = [["Single Iterations"], ["System name", "Score-" + OS_RELEASE]]
        cal_data = [["System name", "Test_passes-" + OS_RELEASE]]
        items = list(items)

        # Sort data by instance size
        sorted_data = sorted(items, key=lambda x: mk_int(process_instance(x[1][0], "size")))

        # Collect cost per hour and price performance data
        cost_per_hour, price_perf_single, price_perf_multi = [], [], []
        for item in sorted_data:
            for index in range(3, len(item)):
                multi_iter.append([item[1][0], item[index][1]])
                single_iter.append([item[1][0], item[index][2]])

                try:
                    cph, ppm = calc_price_performance(item[1][0], item[index][1])
                    cph, pps = calc_price_performance(item[1][0], item[index][2])
                except Exception as exc:
                    custom_logger.error(str(exc))
                    break

                price_perf_multi.append([item[1][0], ppm])
                price_perf_single.append([item[1][0], pps])
                cost_per_hour.append([item[1][0], cph])

        # Prepare the final result for this item
        final_results = [[""]]
        final_results += single_iter
        final_results.append([""])
        final_results.append(["Cost/Hr"])
        final_results += cost_per_hour
        final_results.extend([[""], ["Single Iterations"]])
        final_results.append(["Price-perf", f"Score/$-{OS_RELEASE}"])
        final_results += price_perf_single
        final_results += [[""]]
        final_results += multi_iter
        final_results.extend([[""], ["Multi Iterations"]])
        final_results.append(["Price-perf", f"Score/$-{OS_RELEASE}"])
        final_results += price_perf_multi
        ret_results.extend(final_results)

    return ret_results


def extract_coremark_pro_data(path, system_name, OS_RELEASE):
    """
    Extract CoreMark Pro data from a CSV file, process it, and return the formatted results.

    :param path: Path to the CSV file containing the benchmark results.
    :param system_name: Name of the system being tested.
    :param OS_RELEASE: OS release version (e.g., "Ubuntu 20.04").
    :return: Processed results.
    """
    results = []
    processed_data = []

    # Extract data from file
    try:
        if path.endswith(".csv"):
            with open(path) as file:
                coremark_pro_results = file.readlines()
        else:
            return None, None
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Unable to extract data from csv file for CoreMark Pro")
        return None, None

    data_index = 0
    header = []

    # Parse the CSV data
    for index, data in enumerate(coremark_pro_results):
        if "Test:Multi iterations:Single Iterations:Scaling" in data:
            data_index = index
            header = data.strip("\n").split(":")
        else:
            coremark_pro_results[index] = data.strip("\n").split(":")

    coremark_pro_results = [header] + coremark_pro_results[data_index + 1:]

    # Format the data into the structure we need
    for row in coremark_pro_results:
        if "Test" in row:
            processed_data.append([""])
            processed_data.append([system_name])
            processed_data.append([row[0], row[1], row[2]])
        elif "Score" in row:
            processed_data.append(["Score", row[1], row[2]])

    results.append(processed_data)
    return results
