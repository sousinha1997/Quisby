import re
from itertools import groupby
from typing import List, Optional, Tuple, Union

from quisby import custom_logger
from quisby.pricing.cloud_pricing import get_cloud_pricing
from quisby.util import (
    extract_metadata,
    mk_int,
    process_instance,
    read_config
)


def extract_prefix_and_number(input_string: str) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """
    Extract prefix, number, and suffix from an input string.

    Args:
        input_string (str): String to parse

    Returns:
        Tuple containing (prefix, number, suffix) or (None, None, None) if no match
    """
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)
        return prefix, number, suffix
    return None, None, None


def custom_key(item: Tuple) -> Union[str, Tuple]:
    """
    Generate a custom sorting key based on cloud type and instance characteristics.

    Args:
        item (Tuple): Item to generate key for

    Returns:
        Sorting key based on cloud type
    """
    cloud_type = read_config("cloud", "cloud_type")

    if item[1][0] == "local":
        return item[1][0]
    elif cloud_type == "aws":
        instance_name = item[1][0]
        instance_type, instance_number = instance_name.split(".")
        return instance_type, instance_number
    elif cloud_type == "gcp":
        instance_type = item[1][0].split("-")[0]
        instance_number = int(item[1][0].split('-')[-1])
        return instance_type, instance_number
    elif cloud_type == "azure":
        instance_type, instance_number, version = extract_prefix_and_number(item[1][0])
        return instance_type, version, instance_number


def calc_price_performance(
        instance: str,
        average: float
) -> Tuple[Optional[float], float]:
    """
    Calculate price performance for a given instance.

    Args:
        instance (str): Instance name
        average (float): Performance average

    Returns:
        Tuple of (cost per hour, price performance)
    """
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")

    try:
        cost_per_hour = get_cloud_pricing(
            instance, region, cloud_type.lower(), os_type)
        price_performance = float(average) / float(cost_per_hour)
        return cost_per_hour, price_performance
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Error calculating price performance!")
        return None, 0.0


def group_data(results: List) -> List:
    """
    Group data based on cloud type and instance characteristics.

    Args:
        results (List): Data to be grouped

    Returns:
        Grouped data
    """
    cloud_type = read_config("cloud", "cloud_type")
    cloud_grouping_specs = {
        "aws": lambda x: process_instance(x[1][0], "family", "version", "feature", "machine_type"),
        "azure": lambda x: process_instance(x[1][0], "family", "feature"),
        "gcp": lambda x: process_instance(x[1][0], "family", "version", "sub_family", "feature"),
        "local": lambda x: process_instance(x[1][0], "family")
    }

    if cloud_type == "azure":
        results = sorted(results, key=cloud_grouping_specs["azure"])
        return groupby(results, key=cloud_grouping_specs["azure"])

    return groupby(results, key=cloud_grouping_specs.get(cloud_type, lambda x: x))


def sort_data(results: List) -> None:
    """
    Sort results based on cloud type and instance characteristics.

    Args:
        results (List): List of results to be sorted
    """
    cloud_type = read_config("cloud", "cloud_type")
    sorting_specs = {
        "aws": lambda x: str(process_instance(x[1][0], "family")),
        "azure": lambda x: str(process_instance(x[1][0], "family", "version", "feature")),
        "gcp": lambda x: str(process_instance(x[1][0], "family", "version", "sub_family"))
    }

    results.sort(key=sorting_specs.get(cloud_type, lambda x: x[1][0]))


def extract_coremark_data(
        path: str,
        system_name: str,
        os_release: str
) -> Optional[Tuple[List, List]]:
    """
    Extract CoreMark performance data from a CSV file.

    Args:
        path (str): Path to the CSV file
        system_name (str): Name of the system
        os_release (str): Operating system release version

    Returns:
        Tuple of (processed results, summary data) or None if extraction fails
    """
    results = []
    processed_data = []
    summary_data = []

    server = read_config("server", "name")
    result_dir = read_config("server", "result_dir")

    try:
        if not path.endswith(".csv"):
            return None

        with open(path, 'r') as file:
            coremark_results = [line.strip().split(":") for line in file.readlines()]

        extracted_metadata = extract_metadata(path)
        for index, metadata in enumerate(extracted_metadata):
            print(f"Metadata Block {index + 1}:")
            print(metadata)
            print()

        sum_path = path.split("/./")[1]
        summary_data.append([system_name, f"http://{server}/results/{result_dir}/{sum_path}"])

        # Find header index
        data_index = next(
            (index for index, data in enumerate(coremark_results)
             if "iteration" in str(data)),
            0
        )
        header = coremark_results[data_index]
        coremark_results = [header] + coremark_results[data_index + 1:]

        iteration = 1
        for row in coremark_results:
            if "test passes" in str(row):
                processed_data.extend([[""], [system_name], [row[0], row[2]]])
            else:
                processed_data.append([iteration, row[2]])
                iteration += 1

        results.append(processed_data)
        return results, summary_data

    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Unable to extract data from CSV file for CoreMark")
        return None


def create_summary_coremark_data(
        results: List,
        os_release: str,
        sorted_results: Optional[List] = None
) -> List:
    """
    Create summary data from CoreMark performance results.

    Args:
        results (List): CoreMark test results
        os_release (str): Operating system release version
        sorted_results (Optional[List]): Pre-sorted results

    Returns:
        List of summarized performance data
    """
    final_results = []
    results = list(filter(None, results))
    sort_data(results)

    for _, items in group_data(results):
        cal_data = [["System name", f"Test_passes-{os_release}"]]
        items = list(items)
        sorted_data = sorted(items, key=lambda x: mk_int(process_instance(x[1][0], "size")))

        cost_per_hour, price_per_perf = [], []

        for item in sorted_data:
            # Calculate average performance
            performances = [float(item[index][1]) for index in range(3, len(item))]
            avg_performance = sum(performances) / len(performances)

            try:
                cph, pp = calc_price_performance(item[1][0], avg_performance)
            except Exception as exc:
                custom_logger.error(str(exc))
                break

            cal_data.append([item[1][0], avg_performance])
            price_per_perf.append([item[1][0], pp])
            cost_per_hour.append([item[1][0], cph])

        sorted_results = [[""]] + cal_data
        sorted_results.extend([
            [""],
            ["Cost/Hr"],
            *cost_per_hour,
            [""],
            [f"Price-perf", f"Passes/${os_release}"],
            *price_per_perf
        ])
        final_results.extend(sorted_results)

    return final_results


if __name__ == "__main__":
    # Example usage
    SAMPLE_PATH = "/Users/soumyasinha/Q3/Data/gcp/9.3/9.3/rest/n2-standard-8/pbench-user-benchmark_sousinha_coremark_test__n2-standard-8_2024.01.16T17.58.27/results.csv"
    result, summary = extract_coremark_data(SAMPLE_PATH, "n2-standard-8", "rhel9.2")