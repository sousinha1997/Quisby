import csv
from pquisby.lib.benchmarks.uperf.uperf import extract_uperf_data
from pquisby.lib.util import stream_to_csv
import enum


class InputType(enum.Enum):
    """Various input types"""

    STREAM = enum.auto()
    CSV = enum.auto()
    OTHER_FILE = enum.auto()


class BenchmarkName(enum.Enum):
    """Various benchmark types"""

    UPERF = enum.auto()
    FIO = enum.auto()
    LINPACK = enum.auto()
    SPECJBB = enum.auto()


class QuisbyProcessing:
    def extract_data(self, test_name, dataset_name, input_type, data):
        try:
            if input_type == InputType.STREAM:
                csv_data = stream_to_csv(data)
            elif input_type == InputType.CSV:
                csv_data = data
            elif input_type == InputType.OTHER_FILE:
                with open(data) as csv_file:
                    csv_data = list(csv.reader(csv_file))
            ret_val = []
            json_data = {}
            if test_name == BenchmarkName.UPERF:
                ret_val, json_data = extract_uperf_data(dataset_name, csv_data)
            else:
                pass
        except Exception as exc:
            exception_type = type(exc)
            return {
                "status": "failed",
                "exception": str(exc),
                "exception_type": exception_type,
            }
        return {"status": "success", "csv_data": ret_val, "json_data": json_data}

    def compare_csv_to_json(self, benchmark_name, input_type, data_stream):
        result_json = {}
        comp_dataset_name = ""
        flag = 0
        for dataset_name, data in data_stream.items():
            comp_dataset_name = comp_dataset_name + "&" + dataset_name
            json_res = self.extract_data(benchmark_name, dataset_name, input_type, data)
            if json_res["status"] != "success":
                return json_res

            if json_res["json_data"]:
                json_data = json_res["json_data"]
            if flag == 0:
                result_json = json_data
                flag = flag + 1
            else:
                for i in result_json["data"]:
                    metric_unit = i["metrics_unit"]
                    test_name = i["test_name"]
                    for j in json_data["data"]:
                        if (
                            metric_unit == j["metrics_unit"]
                            and test_name == j["test_name"]
                        ):
                            i["instances"].extend(j["instances"])
        result_json["dataset_name"] = comp_dataset_name
        return {"status": "success", "json_data": result_json}
