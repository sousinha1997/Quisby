import re
from itertools import groupby
from scipy.stats import gmean

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
    gmean_data_intrate = []
    gmean_data_fprate = []
    SYSTEM_GEOMEAN_INTRATE = [[""],["SYSTEM_NAME","GEOMEAN-INTRATE-"+OS_RELEASE]]
    SYSTEM_GEOMEAN_FPRATE = [[""],["SYSTEM_NAME","GEOMEAN-FPRATE-"+OS_RELEASE]]
    for items in sorted_result:
        items = sorted(items, key=custom_key)
        for item in items:
            geomean = 0.0
            for val in range(2,len(item)):
                if item[0][1] == "intrate":
                    gmean_data_intrate.append(float(item[val][1]))
                else:
                    gmean_data_fprate.append(float(item[val][1]))
            if item[0][1] == "intrate":
                geomean = gmean(gmean_data_intrate)
                SYSTEM_GEOMEAN_INTRATE.append([item[0][0], geomean])
            else:
                geomean = gmean(gmean_data_fprate)
                SYSTEM_GEOMEAN_FPRATE.append([item[0][0], geomean])
            results.append([""])
            results += item
    results +=SYSTEM_GEOMEAN_INTRATE
    results +=SYSTEM_GEOMEAN_FPRATE
    return results
