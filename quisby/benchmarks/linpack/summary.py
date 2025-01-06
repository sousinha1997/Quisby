import re
from itertools import groupby
from quisby.util import mk_int, process_instance, read_config


def extract_prefix_and_number(input_string):
    """
    Extracts the prefix, number, and suffix from a given string.

    Args:
        input_string (str): The string to extract the prefix, number, and suffix from.

    Returns:
        tuple: A tuple containing:
            - prefix (str): The prefix part of the string.
            - number (int): The number extracted from the string.
            - suffix (str): The suffix part of the string.
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
    Generates a custom key for sorting/grouping based on the cloud type and item format.

    Args:
        item (tuple): The item to generate the key for. The item is expected to be a tuple
                      where the first element is a string representing the instance type.

    Returns:
        tuple: A tuple used as the sorting/grouping key.
    """
    cloud_type = read_config("cloud", "cloud_type")

    if item[0] == "local":
        return item[0]
    elif cloud_type == "aws":
        instance_type, instance_number = item[0].split(".")[0], item[0].split(".")[1]
        return instance_type, instance_number
    elif cloud_type == "gcp":
        instance_type = item[0].split("-")[0]
        instance_number = int(item[0].split('-')[-1])
        return instance_type, instance_number
    elif cloud_type == "azure":
        instance_type, version, instance_number = extract_prefix_and_number(item[0])
        return instance_type, version, instance_number


def group_data(results):
    """
    Groups the data based on cloud type and instance attributes.

    Args:
        results (list): A list of results that need to be grouped.

    Returns:
        itertools.groupby: A grouped object based on the instance attributes.
    """
    cloud_type = read_config("cloud", "cloud_type")

    if cloud_type == "aws":
        return groupby(results, key=lambda x: process_instance(x[0], "family", "version", "feature", "machine_type"))
    elif cloud_type == "azure":
        results = sorted(results, key=lambda x: process_instance(x[0], "family", "feature"))
        return groupby(results, key=lambda x: process_instance(x[0], "family", "version", "feature"))
    elif cloud_type == "gcp":
        return groupby(results, key=lambda x: process_instance(x[0], "family", "version", "sub_family", "feature"))
    elif cloud_type == "local":
        return groupby(results, key=lambda x: process_instance(x[0], "family"))


def sort_data(results):
    """
    Sorts the results based on cloud type and instance attributes.

    Args:
        results (list): A list of results to be sorted.

    Returns:
        list: The sorted results.
    """
    cloud_type = read_config("cloud", "cloud_type")

    if cloud_type == "aws":
        results.sort(key=lambda x: str(process_instance(x[0], "family")))
    elif cloud_type == "azure":
        results.sort(key=lambda x: str(process_instance(x[0], "family", "version", "feature")))
    elif cloud_type == "gcp":
        results.sort(key=lambda x: str(process_instance(x[0], "family", "version", "sub_family")))
    elif cloud_type == "local":
        return groupby(results, key=lambda x: process_instance(x[0], "family"))


def create_summary_linpack_data(results, os_release):
    """
    Creates a summary of Linpack test data, including GFLOPS, scaling, and cost information.

    Args:
        results (list): The results from the Linpack test that need to be summarized.
        os_release (str): The OS release for which the summary is being created.

    Returns:
        list: The summarized results, including headers and computed values.
    """
    sorted_results = []
    header = [
        [
            "System",
            "Cores",
            f"GFLOPS-{os_release}",
            f"GFLOP Scaling-{os_release}",
            "Cost/hr",
            f"Price-perf-{os_release}",
        ]
    ]

    results = list(filter(None, results))  # Remove any None entries
    sort_data(results)

    for _, items in group_data(results):
        items = list(items)
        sorted_data = sorted(items, key=lambda x: mk_int(process_instance(x[0], "size")))

        cpu_scale, base_gflops = None, None

        for index, row in enumerate(sorted_data):
            if not cpu_scale and not base_gflops:
                cpu_scale = int(row[1])
                base_gflops = float(row[2])
            else:
                try:
                    cpu_scaling = int(row[1]) - cpu_scale
                except ZeroDivisionError:
                    cpu_scaling = 0
                gflops_scaling = float(row[2]) / (int(row[1]) - cpu_scale) / base_gflops if cpu_scaling != 0 else 1
                sorted_data[index][3] = format(gflops_scaling, ".4f")

        res = [item for item in sorted_data]
        sorted_results += header + res

    return sorted_results
