import csv
import logging
from itertools import groupby

from pquisby.pricing.cloud_pricing import get_cloud_pricing
from pquisby.util import mk_int, process_instance, read_config


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
    region = read_config("cloud","region")
    cloud_type = read_config("cloud","cloud_type")
    cost_per_hour, peak_throughput, peak_efficiency = None, None, None
    try:
        cost_per_hour = get_cloud_pricing(
            data[1][0], region, cloud_type.lower())
        peak_throughput = max(data[3:], key=lambda x: int(x[1]))[1]
        peak_efficiency = float(peak_throughput) / float(cost_per_hour)
    except Exception as exc:
        logging.ERROR("Error calculating value !")
    return peak_throughput, cost_per_hour, peak_efficiency


def create_summary_specjbb_data(specjbb_data,OS_RELEASE):
    """"""
    results = []

    specjbb_data = specjbb_sort_data_by_system_family(specjbb_data)

    for items in specjbb_data:
        peak_throughput, cost_per_hour, peak_efficiency = [], [], []

        for item in items:
            results += item
            try:
                pt, cph, pe = calc_peak_throughput_peak_efficiency(item)
            except Exception as exc:
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


def extract_specjbb_data(path, system_name,OS_RELEASE):
    """"""
    results = [[""], [system_name]]

    # File read
    try:
        with open(path) as csv_file:
            specjbb_results = list(csv.DictReader(csv_file, delimiter=":"))
    except Exception as exc:
        return None

    # Find position of SPEC Scores
    # start_index, end_index = 0, 0
    # for index, row in enumerate(specjbb_results):

    #     if "SPEC scores" in row:
    #         start_index = index + 2

    #     if start_index:
    #         if not row.strip("\n"):
    #             end_index = index - 2
    #             break
    results.append(["Warehouses", f"Thrput-{OS_RELEASE}"])
    for data_dict in specjbb_results[1:]:
        if data_dict["Warehouses"] == "Warehouses" or data_dict["Bops"] == "Bops":
            pass
        else:
            results.append([data_dict["Warehouses"], data_dict["Bops"]])
    # # Extract data and convert to a list
    # for row in specjbb_results[start_index:end_index]:
    #     row = row.strip(" ").strip("*").strip(" ").strip("\n").split(" ")

    #     if row[-1] == "Thrput":
    #         row[-1] = row[-1] + f"-{config.OS_RELEASE}"

    #     results.append([row[0], row[-1]])
   
    return results
