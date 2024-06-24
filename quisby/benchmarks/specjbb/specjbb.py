import csv
import re
from itertools import groupby

from quisby import custom_logger
from quisby.pricing.cloud_pricing import get_cloud_pricing
from quisby.util import mk_int, process_instance, read_config


def extract_prefix_and_number(input_string):
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)
        return prefix, number, suffix
    return None, None, None


def custom_key(item):
    cloud_type = read_config("cloud", "cloud_type")
    if item[1][0] == "localhost":
        return item[1][0]
    elif cloud_type == "aws":
        instance_type =item[1][0].split(".")[0]
        instance_number = item[1][0].split(".")[1]
        return instance_type, instance_number
    elif cloud_type == "gcp":
         instance_type = item[1][0].split("-")[0]
         instance_number = int(item[1][0].split('-')[-1])
         return instance_type, instance_number
    elif cloud_type == "azure":
        instance_type, instance_number, version= extract_prefix_and_number(item[1][0])
        return instance_type, instance_number


def specjbb_sort_data_by_system_family(results):
    sorted_result = []

    results.sort(key=lambda x: str(process_instance(
        x[1][0], "family", "version", "feature")))

    for _, items in groupby(results, key=lambda x: process_instance(x[1][0], "family", "version", "feature")):
        sorted_result.append(
            sorted(list(items), key=lambda x: mk_int(
                process_instance(x[1][0], "size")))
        )

    return sorted_result


def calc_peak_throughput_peak_efficiency(data):
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")
    cost_per_hour, peak_throughput, peak_efficiency = None, None, None
    try:
        cost_per_hour = get_cloud_pricing(
            data[1][0], region, cloud_type.lower(), os_type)
        peak_throughput = max(data[3:], key=lambda x: int(x[1]))[1]
        peak_efficiency = float(peak_throughput) / float(cost_per_hour)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Error calculating value !")
    return peak_throughput, cost_per_hour, peak_efficiency


def create_summary_specjbb_data(specjbb_data, OS_RELEASE):
    """"""
    results = []

    specjbb_data = specjbb_sort_data_by_system_family(specjbb_data)

    for items in specjbb_data:
        peak_throughput, cost_per_hour, peak_efficiency = [], [], []
        sorted_data = sorted(items, key=custom_key)
        for item in sorted_data:
            results += item
            try:
                pt, cph, pe = calc_peak_throughput_peak_efficiency(item)
            except Exception as exc:
                custom_logger.error(str(exc))
                break
            peak_throughput.append([item[1][0], pt])
            cost_per_hour.append([item[1][0], cph])
            peak_efficiency.append([item[1][0], pe])

        results.append([""])
        results.append(["Peak", f"Thrput-{OS_RELEASE}"])
        results += peak_throughput
        results.append([""])
        results.append(["Cost/Hr"])
        results += cost_per_hour
        results.append([""])
        results.append(["Peak/$eff", f"Price/perf-{OS_RELEASE}"])
        results += peak_efficiency

    return results


def extract_specjbb_data(path, system_name, OS_RELEASE):
    """"""
    results = [[""], [system_name]]

    # File read
    try:
        if path.endswith(".csv"):
            with open(path) as csv_file:
                specjbb_results = list(csv.DictReader(csv_file, delimiter=":"))
        else:
            return None
    except Exception as exc:
        custom_logger.error(str(exc))
        return None

    results.append(["Warehouses", f"Thrput-{OS_RELEASE}"])
    for data_dict in specjbb_results[1:]:
        if data_dict["Warehouses"] == "Warehouses" or data_dict["Bops"] == "Bops":
            pass
        else:
            results.append([data_dict["Warehouses"], data_dict["Bops"]])

    return results
