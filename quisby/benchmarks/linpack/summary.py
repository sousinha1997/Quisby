import re
from itertools import groupby

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
    cloud_type = read_config("cloud","cloud_type")
    if item[0] == "localhost":
        return item[0]
    elif cloud_type == "aws":
        instance_type =item[0].split(".")[0]
        instance_number = item[0].split(".")[1]
        return instance_type, instance_number
    elif cloud_type == "gcp":
         instance_type = item[0].split("-")[0]
         instance_number = int(item[0].split('-')[-1])
         return instance_type, instance_number
    elif cloud_type == "azure":
        instance_type, instance_number, version=extract_prefix_and_number(item[0])
        return instance_type, instance_number


def create_summary_linpack_data(results, OS_RELEASE):
    sorted_results = []

    results = list(filter(None, results))
    header_row = [results[0]]
    results = [row for row in results if row[0] != "System"]

    results.sort(key=lambda x: str(process_instance(x[0], "family", "version", "feature")))

    for _, items in groupby(results, key=lambda x: process_instance(x[0], "family", "version", "feature")):
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
        sorted_data = sorted(sorted_data, key=custom_key)
        res = []
        for item in sorted_data:
            res.append(item)
        sorted_results += header_row + res
        # sorted_results += header_row + sorted_data

    return sorted_results
