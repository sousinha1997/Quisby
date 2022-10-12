import csv
import logging
from itertools import groupby

import requests

import quisby.config as config
from quisby.util import mk_int, process_instance


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


def create_summary_uperf_data(results):
    summary_results = []
    group_by_test_name = {}

    sorted_results = uperf_sort_data_by_system_family(results)

    for result in sorted_results:
        for row in result:
            key = row[1][0].split(".")[0] + "-" + row[2][0] + "-" + row[3][1]
            if key in group_by_test_name:
                group_by_test_name[key].append(row)
            else:
                group_by_test_name[key] = [row]

    for key, value in group_by_test_name.items():
        run_data = {}
        test_identifier = key.rsplit("-", 2)

        summary_results.append([""])
        summary_results.append(test_identifier)
        summary_results.append(["Instance Count"])

        for ele in value:
            summary_results[-1].append(ele[1][0] + "-" + config.OS_RELEASE)
            for index in ele[4:]:
                if index[0] in run_data:
                    run_data[index[0]].append(index[1].strip())
                else:
                    run_data[index[0]] = [index[1].strip()]

        for instance_count_data in value[0][4:]:
            summary_results.append(
                [instance_count_data[0], *run_data[instance_count_data[0]]]
            )

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
    except requests.exceptions.InvalidSchema:
        with open(path) as csv_file:
            csv_reader = list(csv.reader(csv_file))

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


if __name__ == "__main__":
    print(
        extract_uperf_data(
            "uperf_results_8.3/user_none_instance_m5a.24xlarge:Networks_number=1_/result.csv",
            "i3en.xlarge",
        )
    )
