import re
from itertools import groupby

from quisby.util import mk_int, process_instance, read_config

from quisby import custom_logger

from quisby.pricing.cloud_pricing import get_cloud_pricing


def extract_prefix_and_number(input_string):
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)
        return prefix, number, suffix
    return None, None, None


def get_inst_name(item):
    cloud_type = read_config("cloud", "cloud_type")
    if item == "local":
        return item
    elif cloud_type == "aws":
        instance =item.split("-")[0]
        return instance
    elif cloud_type == "gcp":
         ll= item.split("-")
         instance = ll[0]+"-"+ll[1]+"-"+ll[2]
         return instance
    elif cloud_type == "azure":
        instance =item.split("-")[0]
        return instance


def hammerdb_sort_data_by_system_family(results):
    sorted_result = []

    results = [list(g) for k, g in groupby(results, key=lambda x: x != [""]) if k]

    results.sort(key=lambda x: str(process_instance(x[0][1], "family", "version", "feature")))

    for _, items in groupby(results, key=lambda x: process_instance(x[0][1], "family", "version", "feature")):
        items = list(items)
        sorted_result.append(sorted(items, key=lambda x: mk_int(process_instance(x[0][1], "size"))))

    return sorted_result

# def hammerdb_sort_data_by_system_family(results):
#     sorted_result = []
#
#     results = [list(g) for k, g in groupby(results, key=lambda x: x != [""]) if k]
#
#     results.sort(key=lambda x: str(process_instance(x[0][1], "family", "version", "feature")))
#
#     for _, items in group_data(results):
#         sorted_result += sorted(
#             list(items), key=lambda x: mk_int(process_instance(x[0][1], "size"))
#         )
#
#     return sorted_result


def calc_price_performance(inst, avg):
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")
    cost_per_hour = None
    price_perf = None
    try:
        cost_per_hour = get_cloud_pricing(
            inst, region, cloud_type.lower(), os_type)
        price_perf = float(avg)/float(cost_per_hour)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Error calculating value !")
        cost_per_hour = 0.0
        price_perf = 0.0
    return cost_per_hour, price_perf


def create_summary_hammerdb_data(hammerdb_data):
    results = []

    hammerdb_data = hammerdb_sort_data_by_system_family(hammerdb_data)

    for data in hammerdb_data:
        run_data = {}
        price_per_perf = {}
        results.append([""])
        results.append([data[0][0][0]])
        price_results = []
        price_results += [[""],["Price-Perf"]]
        cost_per_hour = []

        for row in data:
            inst = get_inst_name(row[0][1])
            results[-1] += [row[0][1]]
            price_results[-1] += [row[0][1]]
            cph = 0.0
            pp = 0.0
            for ele in row[1:]:
                try:
                    cph, pp = calc_price_performance(inst, int(ele[1].strip()))
                except Exception as exc:
                    custom_logger.error(str(exc))
                    cph = 0.0
                    pp = 0.0

                if ele[0] in run_data:
                    run_data[ele[0]].append(ele[1])
                else:
                    run_data[ele[0]] = [ele[1]]

                if ele[0] in price_per_perf:
                    price_per_perf[ele[0]].append(pp)
                else:
                    price_per_perf[ele[0]] = [pp]

            cost_per_hour.append([inst, cph])

        for key, item in run_data.items():
            results.append([key, *item])

        results += [[''], ['Cost/Hr'] ] + cost_per_hour

        results +=price_results
        for key, item in price_per_perf.items():
            results.append([key, *item])

    return results
