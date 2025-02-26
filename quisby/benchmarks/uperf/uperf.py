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

        if test_identifier[-1] == "GB_Sec":
            price_results.append([""])
            price_results.append(["Price-Perf",test_identifier[1], "GB_Sec/$"])
            price_results.append(["Instance Count"])

        for ele in value:
            inst = ele[1][0]
            summary_results[-1].append(ele[1][0] + "-" + OS_RELEASE)
            if test_identifier[-1] == "GB_Sec":
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

def split_into_parts(data):
    result = []
    temp = []

    # Iterate through the data
    for item in data:
        if item == "#Test general meta start\n":
            if temp:
                result.append(temp)
                temp = []
        else:
            temp.append(item)

    # Append the last group if it's not empty
    if temp:
        result.append(temp)
    return result


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
        with open(path) as csv_file:
            csv_data = csv_file.readlines()

    csv_reader = split_into_parts(csv_data)

    result = []
    test_type = ""
    packet_type = ""
    packet_size = ""
    metric = ""
    header_line_index = []
    for data in csv_reader:
        for i, line in enumerate(data):
            if line.startswith('Instance_Count:'):
                metric = line.split(":")[-1].strip()
                header_line_index.append((i,metric))

    for index,metric in header_line_index:
        data_lines = csv_data[index + 1:index + 4]
        try:
            instance_data = []
            for line in data_lines:
                # Split the values in the format '1:1:1:641169.83'
                values = line.split(":")
                if len(values) == 5:  # If the line contains the expected format
                    intance_count, value, test_type, packet_type, packet_size = values
                    instance_data.append([f"{intance_count}i", value.strip()])
        except Exception as exc:
            custom_logger.debug(str(exc))
            custom_logger.error("Data format incorrect. Skipping data")
        results.append([""])
        results.append([system_name])
        results.append([f"{packet_type}_{test_type}{packet_size.strip()}"])
        results.append(["Instance Count", metric])
        results.extend(instance_data)
    return results


