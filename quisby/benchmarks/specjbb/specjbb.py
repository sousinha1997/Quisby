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
    if item[1][0] == "local":
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
        return instance_type,version, instance_number


def group_data(results):
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "aws":
        return groupby(results, key=lambda x: process_instance(x[1][0], "family", "version", "feature", "machine_type"))
    elif cloud_type == "azure":
        results = sorted(results, key=lambda x: process_instance(x[1][0], "family", "feature"))
        return groupby(results, key=lambda x: process_instance(x[1][0], "family", "version", "feature"))
    elif cloud_type == "gcp":
        return groupby(results, key=lambda x: process_instance(x[1][0], "family", "version","sub_family","feature"))
    elif cloud_type == "local":
        return groupby(results, key=lambda x: process_instance(x[1][0], "family"))

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
        custom_logger.error("Error calculating value for :" + data[1][0])
    return peak_throughput, cost_per_hour, peak_efficiency



def sort_data(results):
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "aws":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family")))
    elif cloud_type == "azure":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "feature")))
    elif cloud_type == "gcp":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "sub_family")))

def create_summary_specjbb_data(specjbb_data, OS_RELEASE):
    """"""

    results = []
    #specjbb_data = specjbb_sort_data_by_system_family(specjbb_data)
    specjbb_data = list(filter(None, specjbb_data))
    sort_data(specjbb_data)
    specjbb_data = group_data(specjbb_data)

    for _,items in specjbb_data:
        items = list(items)
        peak_throughput, cost_per_hour, peak_efficiency = [], [], []
        sorted_data = sorted(items, key=lambda x: mk_int(process_instance(x[1][0], "size")))
        for item in sorted_data:
            results.extend(item)
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
        results.append(["Peak/$eff", f"Price-perf-{OS_RELEASE}"])
        results += peak_efficiency

    return results


def extract_specjbb_data(path, system_name, OS_RELEASE):
    """"""
    results = [[""], [system_name]]
    summary_data = []
    server = read_config("server", "name")
    result_dir = read_config("server", "result_dir")

    # File read
    try:
        if path.endswith(".csv"):
            with open(path) as csv_file:
                specjbb_results = list(csv.DictReader(csv_file, delimiter=":"))
            sum_path = path.split("/./")[1]
            summary_data.append([system_name, "http://" + server + "/results/" + result_dir + "/" + sum_path])
        else:
            return None
    except Exception as exc:
        custom_logger.error(str(exc))
        return None, None

    results.append(["Warehouses", f"Thrput-{OS_RELEASE}"])
    for data_dict in specjbb_results[1:]:
        if data_dict["Warehouses"] == "Warehouses" or data_dict["Bops"] == "Bops":
            pass
        else:
            results.append([data_dict["Warehouses"], data_dict["Bops"]])

    return results, summary_data
