import re
from itertools import groupby

from quisby.util import mk_int, process_instance, read_config
from quisby import custom_logger
from quisby.pricing.cloud_pricing import get_cloud_pricing
from scipy.stats import gmean


def extract_prefix_and_number(input_string):
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)
        return prefix, number, suffix
    return None, None, None


def custom_key(item):
    cloud_type = read_config("cloud","cloud_type")
    if item[0][0] == "local":
        return item[0][0]
    elif cloud_type == "aws":
        instance_type =item[0][0].split(".")[0]
        instance_number = item[0][0].split(".")[1]
        return instance_type, instance_number
    elif cloud_type == "gcp":
         instance_type = item[0][0].split("-")[0]
         instance_number = int(item[0][0].split('-')[-1])
         return instance_type, instance_number
    elif cloud_type == "azure":
        instance_type, instance_number, version=extract_prefix_and_number(item[0][0])
        return instance_type, version, instance_number


def group_data(results):
    cloud_type = read_config("cloud", "cloud_type")
    if cloud_type == "aws":
        return groupby(results, key=lambda x: process_instance(x[0][0], "family", "feature", "machine_type"))
    elif cloud_type == "azure":
        results = sorted(results, key=lambda x: process_instance(x[0][0], "family", "feature"))
        return groupby(results, key=lambda x: process_instance(x[0][0], "family", "feature"))
    elif cloud_type == "gcp":
        return groupby(results, key=lambda x: process_instance(x[0][0], "family","sub_family","feature"))
    elif cloud_type == "local":
        return groupby(results, key=lambda x: process_instance(x[0][0], "family"))


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


def create_summary_speccpu_data(results, OS_RELEASE):
    sorted_result = []
    results = [list(g) for k, g in groupby(results, key=lambda x: x != [""]) if k]
    sorted_result =  list(filter(None, results))
    results = []
    for _,items in group_data(sorted_result):
        cost_per_hour, price_perf_int, price_perf_float = [], [], []
        gmean_results_intrate = []
        gmean_results_fprate = []
        start_index = 0
        test = ""
        items = list(items)
        sorted_data = sorted(items, key=lambda x: mk_int(process_instance(x[0][0], "size")))
        for item in sorted_data:
            i_gmean = []
            f_gmean = []
            test = item[0][1]
            for i in range(3, len(item)):
                if test == "intrate":
                    i_gmean.append(float(item[i][1]))
                elif test == "fprate":
                    f_gmean.append(float(item[i][1]))
            if i_gmean:
                i_gmean = gmean(i_gmean)
                gmean_results_intrate.append([item[0][0], i_gmean])
            if f_gmean:
                f_gmean = gmean(f_gmean)
                gmean_results_fprate.append([item[0][0], f_gmean])

            cphi = []
            cphf = []
            try:
                if item[0][1] == "intrate":
                    cphi, ppi = calc_price_performance(item[0][0], i_gmean)
                    price_perf_int.append([item[0][0], ppi])
                    if [item[0][0], cphi] not in cost_per_hour:
                        cost_per_hour.append([item[0][0], cphi])
                elif item[0][1] == "fprate":
                    cphf, ppf = calc_price_performance(item[0][0], f_gmean)
                    price_perf_float.append([item[0][0], ppf])
                    if [item[0][0], cphf] not in cost_per_hour:
                        cost_per_hour.append([item[0][0], cphf])
            except Exception as exc:
                custom_logger.error(str(exc))
                break
        results.append([""])
        results.append(["Cost/Hr"])
        results += cost_per_hour
        if gmean_results_intrate :
            results.append([""])
            results.append(["System name", "Geomean_intrate-" + OS_RELEASE])
            results += gmean_results_intrate
            results.extend([[""]])
            results.append(["Price-perf", f"Geomean_intrate/$-{OS_RELEASE}"])
            results += price_perf_int
        if gmean_results_fprate:
            results.append([""])
            results.append(["System name", "Geomean_fprate-" + OS_RELEASE])
            results += gmean_results_fprate
            results.extend([[""]])
            results.append(["Price-perf", f"Geomean_fprate/$-{OS_RELEASE}"])
            results += price_perf_float
    return results