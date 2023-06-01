import csv
from pquisby.lib.benchmarks.uperf.uperf import extract_uperf_data
from pquisby.lib.util import read_config, stream_to_csv


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