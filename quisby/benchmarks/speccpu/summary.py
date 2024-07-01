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
    if item[0][0] == "localhost":
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
        return instance_type, instance_number


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
    results.sort(
        key=lambda x: str(process_instance(x[0][0], "family", "version", "feature"))
    )

    for _, items in groupby(
            results, key=lambda x: process_instance(x[0][0], "family", "version", "feature")
    ):
        sorted_result.append(
            sorted(list(items), key=lambda x: mk_int(process_instance(x[0][0], "size")))
        )

    results = []

    cost_per_hour, price_perf_int, price_perf_float = [], [], []
    for items in sorted_result:
        items = sorted(items, key=custom_key)
        i_gmean = []
        f_gmean = []
        start_index = 0
        test = ""
        for item in items:
            test = item[0][1]
            results.append([""])
            results += item
            for i in range(2, len(item)):
                if test == "intrate":
                    i_gmean.append(float(item[i][1]))
                elif test == "fprate":
                    f_gmean.append(float(item[i][1]))

        i_gmean = gmean(i_gmean)
        f_gmean = gmean(f_gmean)
        cph = []
        for item in items:
            try:
                if item[0][1] == "intrate":
                    cph, ppi = calc_price_performance(item[0][0], i_gmean)
                    price_perf_int.append([item[0][0], ppi])
                    cost_per_hour.append([item[0][0], cph])
                elif item[0][1] == "fprate":
                    cph, ppf = calc_price_performance(item[0][0], f_gmean)
                    price_perf_float.append([item[0][0], ppf])
            except Exception as exc:
                custom_logger.error(str(exc))
                break


    results.append([""])
    results.append(["Cost/Hr"])
    results += cost_per_hour
    results.extend([[""], ["intrate"]])
    results.append(["Price/perf", f"int-{OS_RELEASE}"])
    results += price_perf_int
    results.extend([[""], ["fprate"]])
    results.append(["Price/perf", f"float-{OS_RELEASE}"])
    results += price_perf_float
    return results
