from itertools import groupby

from scipy.stats import gmean

from quisby import custom_logger
from quisby.util import read_config
from quisby.pricing.cloud_pricing import get_cloud_pricing
import re

from quisby.util import process_instance, mk_int

from quisby.sheet.sheet_util import append_to_sheet


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
        instance_type, instance_number, version= extract_prefix_and_number(item[0])
        return instance_type, version, instance_number


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



def sort_data(results):
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "aws":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family")))
    elif cloud_type == "azure":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "feature")))
    elif cloud_type == "gcp":
        results.sort(key=lambda x: str(process_instance(x[1][0], "family", "version", "sub_family")))


def create_summary_pyperf_data(data, OS_RELEASE):
    ret_results = []

    results = list(filter(None, data))
    sort_data(results)
    results = group_data(results)
    for _, items in results:
        mac_data = [["System name", "Geomean-" + OS_RELEASE]]
        cost_data = [["Cost/Hr"]]
        price_perf_data = [["Price-perf",f"Geomean/$-{OS_RELEASE}"]]
        items = list(items)
        sorted_data = sorted(items, key=lambda x: mk_int(process_instance(x[1][0], "size")))
        cost_per_hour, price_per_perf = [], []
        # Add summary data
        for index, row in enumerate(sorted_data):
            inst = row[1][0]
            gmean_data=[]
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
    """"""
    results = []
    server = read_config("server", "name")
    result_dir = read_config("server", "result_dir")
    # Extract data from file
    summary_data = []
    try:
        if path:
            with open(path) as file:
                pyperf_results = file.readlines()
                sum_path = path.split("/./")[1]
                summary_data.append([system_name, "http://"+server+"/results/"+result_dir+"/"+sum_path])
        else:
            return None
    except Exception as exc:
        custom_logger.error(str(exc))
        return None
    for index, data in enumerate(pyperf_results):
        pyperf_results[index] = data.strip("\n").split(":")
    results.append([""])
    results.append([system_name])
    results.extend(pyperf_results[1:])
    return [results], summary_data