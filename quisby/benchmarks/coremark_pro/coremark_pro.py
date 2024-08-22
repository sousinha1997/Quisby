import re

from quisby import custom_logger
from quisby.util import read_config
from quisby.pricing.cloud_pricing import get_cloud_pricing


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
    try:
        if item[1][0] == "localhost":
            return item[1][0]
        elif cloud_type == "aws":
            instance_type = item[1][0].split(".")[0]
            instance_number = item[1][0].split(".")[1]
            return instance_type, instance_number
        elif cloud_type == "gcp":
            instance_type = item[1][0].split("-")[0]
            instance_number = int(item[1][0].split('-')[-1])
            return instance_type, instance_number
        elif cloud_type == "azure":
            instance_type, instance_number, version = extract_prefix_and_number(item[1][0])
            return instance_type, instance_number
    except Exception as exc:
        custom_logger.error(str(exc))
        return "", ""


def calc_price_performance(inst, avg):
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")
    cost_per_hour = None
    try:
        cost_per_hour = get_cloud_pricing(
            inst, region, cloud_type.lower(), os_type)
        price_perf = float(avg)/float(cost_per_hour)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Error calculating value !")
    return cost_per_hour, price_perf


def create_summary_coremark_pro_data(results, OS_RELEASE):
    final_results = []
    multi_iter = [["Multi Iterations"], ["System name", "Score-" + OS_RELEASE]]
    single_iter = [["Single Iterations"], ["System name", "Score-" + OS_RELEASE]]
    # Sort data based on instance name
    sorted_data = sorted(results, key=custom_key)
    # Add summary data
    cost_per_hour, price_perf_single, price_perf_multi = [], [],[]
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
            # final_results += item
    final_results += [[""]]
    final_results += single_iter
    final_results.append([""])
    final_results.append(["Cost/Hr"])
    final_results += cost_per_hour
    final_results.extend([[""], ["Single Iterations"]])
    final_results.append(["Price/perf", f"Score/$-{OS_RELEASE}"])
    final_results += price_perf_single
    final_results += [[""]]
    final_results += multi_iter
    final_results.extend([[""], ["Multi Iterations"]])
    final_results.append(["Price/perf", f"Score/$-{OS_RELEASE}"])
    final_results += price_perf_multi
    return final_results


def extract_coremark_pro_data(path, system_name, OS_RELEASE):
    """"""
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
        custom_logger.error("Unable to extract data from csv file for coremark_pro")
        return None

    for index, data in enumerate(coremark_results):
        coremark_results[index] = data.strip("\n").split(":")

    # Format the data
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