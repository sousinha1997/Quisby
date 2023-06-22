from itertools import groupby

def combine_uperf_data(results):
    result_data = []
    group_data = []

    for data in results:
        if data == [""]:
            group_data.append(result_data)
            result_data = []
        if data:
            result_data.append(data)
    # Last data point insertion
    group_data.append(result_data)
    group_data.remove([])
    return group_data


def create_summary_uperf_data(results, run_name, OS_RELEASE):
    summary_results = []
    group_by_test_name = {}
    sorted_results = [combine_uperf_data(results)]
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
            summary_results[-1].append(run_name + "-os-release-" + OS_RELEASE)
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


def extract_uperf_data(dataset_name, csv_data):
    """"""
    results = []
    data_position = {}
    results_json = {"dataset_name": "", "data": []}
    tests_supported = ["tcp_stream", "tcp_rr", "tcp_bidirec", "tcp_maerts"]

    for index, row in enumerate(csv_data[0]):
        if "all" in row:
            data_position[row.split(":")[0]] = index
    filtered_result = []
    # Keep only required test results
    csv_reader = list(filter(None, csv_data))
    for result in csv_reader:
        try:
            if result[1].split("-")[0] in tests_supported:
                filtered_result.append(result)
        except Exception as exc:
            pass
    # filtered_result = list(filter(lambda x: x[1].split("-")[0] in tests_supported, csv_reader))
    # Group data by test name and pkt size
    for test_name, items in groupby(filtered_result, key=lambda x: x[1].split("-")[:2]):
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
                        data_dict[key] = [[instance_count, item[data_position[key]]]]

        for key, test_results in data_dict.items():
            test_json = {
                "vm_name": "",
                "test_name": "",
                "metrics_unit": "",
                "instances": [],
            }
            if test_results:
                test_json["test_name"] = "".join(test_name)
                test_json["metrics_unit"] = key
                results.append([""])
                results.append(["".join(test_name)])
                results.append(["Instance Count", key])
                for instance_count, items in groupby(
                    test_results, key=lambda x: x[0].split("-")[0]
                ):
                    items = list(items)
                    item_json = {}
                    item_json["name"] = instance_count
                    item_json["dataset_name"] = dataset_name
                    if len(items) > 1:
                        failed_run = True
                        for item in items:
                            if "fail" not in item[0]:
                                item_json["status"] = "pass"
                                item_json["time_taken"] = item[0]
                                test_json["instances"].append(item_json)
                                results.append(item)
                                failed_run = False
                                break
                        if failed_run:
                            item_json["status"] = "fail"
                            item_json["time_taken"] = "fail"
                            test_json["instances"].append(item_json)
                            results.append([instance_count, "fail"])
                    else:
                        item_json["status"] = "pass"
                        item_json["time_taken"] = items[0][1]
                        test_json["instances"].append(item_json)
                        results.append(*items)
            results_json["data"].append(test_json)
        results_json["dataset_name"] = dataset_name
    return results, results_json


if __name__ == "__main__":
    print(
        extract_uperf_data(
            "localhost",
            "/Users/soumyasinha/Workspace/2022/rocky_rhel_gvnic/hackathon/pbench.perf.lab.eng.bos.redhat.com/results/pravins.localhost/uperf__2022.10.07T06.49.32/results_uperf.csv",
        )
    )
