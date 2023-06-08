import csv
from pquisby.lib.benchmarks.uperf.uperf import extract_uperf_data
from pquisby.lib.util import stream_to_csv


def extract_data(test_name, dataset_name, system_name, input_type, data):
    try:
        if input_type == "stream":
            csv_data = stream_to_csv(data)
        elif input_type == "csv":
            csv_data = data
        elif input_type == "file":
            with open(data) as csv_file:
                csv_data = list(csv.reader(csv_file))
        ret_val = []
        json_data = {}
        if test_name == "uperf":
            ret_val, json_data = extract_uperf_data(dataset_name, system_name, csv_data)
        else:
            pass
    except Exception as exc:
        exception_type = type(exc)
        return {"status": "failed", "Exception": str(exc), "Exception_type": exception_type}
    return {"status": "success", "csvData": ret_val, "jsonData": json_data}


def compare_csv_to_json(benchmark_name, input_type, data_stream):
    result_json = {}
    flag = 0
    for dataset_name, data in data_stream.items():
        json_res = extract_data(benchmark_name, dataset_name, "baremetal", input_type, data)
        if json_res["jsonData"]:
            json_data = json_res["jsonData"]
        if flag == 0:
            result_json = json_data
            flag = flag + 1
        else:
            for i in result_json["data"]:
                metric_unit = i["metrics_unit"]
                test_name = i["test_name"]
                for j in json_data["data"]:
                    if metric_unit == j["metrics_unit"] and test_name == j["test_name"]:
                        i["instances"].extend(j["instances"])
    return result_json
