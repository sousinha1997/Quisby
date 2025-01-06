import csv
import re
from itertools import groupby

import requests

from quisby.util import read_config

from quisby.util import mk_int, process_instance

from quisby import custom_logger
from quisby.benchmarks.coremark.coremark import calc_price_performance
from quisby.util import read_config


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
        return instance_type, version, instance_number


def combine_uperf_data(results):
    result_data = []
    group_data = []

    for data in results:
        if data == ['']:
            group_data.append(result_data)
            result_data = []
        if data:
            result_data.append(data)
    # Last data point insertion
    group_data.append(result_data)
    group_data.remove([])
    return group_data


def create_summary_uperf_data(results, OS_RELEASE):
    summary_results = []

    group_by_test_name = {}

    sorted_results = [combine_uperf_data(results)]

    for result in sorted_results:
        result = sorted(list(result), key=lambda x: mk_int(process_instance(x[1][0], "size")))
        for row in result:
            key = row[1][0] + "-" + row[2][0] + "-" + row[3][1]
            if key in group_by_test_name:
                group_by_test_name[key].append(row)
            else:
                group_by_test_name[key] = [row]

    for key, value in group_by_test_name.items():
        run_data = {}
        price_per_perf = {}
        price_results = []
        cost_per_hour = []
        test_identifier = key.rsplit("-", 2)
        cph = 0.0
        pp = 0.0

        summary_results.append([""])
        summary_results.append(test_identifier)
        summary_results.append(["Instance Count"])

        if test_identifier[-1] == "Gb_sec":
            price_results.append([""])
            price_results.append(["Price-Perf",test_identifier[0],test_identifier[1], "Gb_sec/$"])
            price_results.append(["Instance Count"])

        for ele in value:
            inst = ele[1][0]
            summary_results[-1].append(ele[1][0] + "-" + OS_RELEASE)
            if test_identifier[-1] == "Gb_sec":
                price_results[-1].append(ele[1][0] + "-" + OS_RELEASE)

            for index in ele[4:]:
                if index[0] in run_data:
                    run_data[index[0]].append(index[1].strip())
                else:
                    run_data[index[0]] = [index[1].strip()]

                if price_results:
                    try:
                        cph, pp = calc_price_performance(inst, float(index[1].strip()))
                    except Exception as exc:
                        custom_logger.error(str(exc))
                        cph = 0.0
                        pp = 0.0

                    if index[0] in price_per_perf:
                        price_per_perf[index[0]].append(pp)
                    else:
                        price_per_perf[index[0]] = [pp]

            cost_per_hour.append([inst, cph])


        for instance_count_data in value[0][4:]:
            summary_results.append(
                [instance_count_data[0], *run_data[instance_count_data[0]]]
            )

        if price_results:
            summary_results += [[''], ['Cost/Hr']] + cost_per_hour

        summary_results += price_results
        for key, item in price_per_perf.items():
            summary_results.append([key, *item])

    return summary_results


def extract_uperf_data(path, system_name):
    """"""
    results = []
    data_position = {}

    tests_supported = ["tcp_stream", "tcp_rr"]

    # Check if path is a URL
    try:
        csv_data = requests.get(path)
        csv_reader = list(csv.reader(csv_data.text.split("\n")))
    except Exception:
        if path.endswith("result.csv"):
            with open(path) as csv_file:
                csv_reader = list(csv.reader(csv_file))
        else:
            return None

    # find all ports result index in csv row
    for index, row in enumerate(csv_reader[0]):
        if "all" in row:
            data_position[row.split(":")[0]] = index

    # Keep only tcp_stream and tcp_rr test results
    csv_reader = list(filter(None, csv_reader))
    filtered_result = list(
        filter(lambda x: x[1].split("-")[0] in tests_supported, csv_reader)
    )

    # Group data by test name and pkt size
    for test_name, items in groupby(
            filtered_result, key=lambda x: x[1].split("-")[:2]
    ):
        data_dict = {}

        for item in items:
            instance_count = "-".join(item[1].split("-")[2:])

            # Extract BW, trans_sec & latency data
            for key in data_position.keys():

                if item[data_position[key]]:
                    if key in data_dict:
                        data_dict[key].append(
                            [instance_count, item[data_position[key]]]
                        )
                    else:
                        data_dict[key] = [
                            [instance_count, item[data_position[key]]]
                        ]

        for key, test_results in data_dict.items():
            if test_results:
                results.append([""])
                results.append([system_name])
                results.append(["".join(test_name)])
                results.append(["Instance Count", key])
                for instance_count, items in groupby(
                        test_results, key=lambda x: x[0].split("-")[0]
                ):
                    items = list(items)

                    if len(items) > 1:
                        failed_run = True
                        for item in items:
                            if "fail" not in item[0]:
                                results.append(item)
                                failed_run = False
                                break
                        if failed_run:
                            results.append([instance_count, "fail"])
                    else:
                        results.append(*items)

    return results


