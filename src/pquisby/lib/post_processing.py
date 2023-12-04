import csv
import logging

from pquisby.lib.benchmarks.fio.fio import extract_fio_run_data
from pquisby.lib.benchmarks.uperf.uperf import extract_uperf_data
from pquisby.lib.logging import logging_configure
from pquisby.lib.util import stream_to_csv
import enum

logging_configure.configure_logging()

class InputType(enum.Enum):
    """Various input types"""

    STREAM = enum.auto()
    CSV = enum.auto()
    OTHER_FILE = enum.auto()


class BenchmarkName(enum.Enum):
    """Various benchmark types"""

    UPERF = enum.auto()
    FIO = enum.auto()


    """Uncomment or add more benchmark once we are ready with other benchmarks."""
    # SPECJBB = enum.auto()
    # LINPACK = enum.auto()


class QuisbyProcessing:
    def extract_data(self, test_name, dataset_name, input_type, data):
        logging.info("********************** Starting preprocessing of data **********************")
        logging.info("Input Type: " + str(input_type))
        logging.info("Benchmark Type: " + str(test_name))
        logging.info("Dataset Name: " + str(dataset_name))
        try:
            path = ""
            if input_type == InputType.STREAM:
                csv_data = stream_to_csv(data)
            elif input_type == InputType.CSV:
                csv_data = data
            elif input_type == InputType.OTHER_FILE:
                with open(data) as csv_file:
                    if test_name == BenchmarkName.UPERF:
                        csv_data = list(csv.reader(csv_file))
                    elif test_name == BenchmarkName.FIO:
                        csv_data = csv_file.readlines()
                        csv_data[-1] = csv_data[-1].strip()
                        for i in range(0,len(csv_data)):
                            csv_data[i]=csv_data[i].split(",")

            ret_val = []
            json_data = {}
            logging.info("Start extraction...")
            if test_name == BenchmarkName.UPERF:
                ret_val, json_data = extract_uperf_data(dataset_name, csv_data)
            if test_name == BenchmarkName.FIO:
                ret_val, json_data = extract_fio_run_data(dataset_name, csv_data, path)
            else:
                pass
        except Exception as exc:
            logging.info("!!! PREPROCESSING FAILED !!!")
            exception_type = type(exc)
            return {
                "status": "failed",
                "exception": str(exc),
                "exception_type": exception_type,
            }
        logging.info("!!! PREPROCESSING COMPLETE !!!")
        return {"status": "success", "csv_data": ret_val, "json_data": json_data}

    def compare_csv_to_json(self, benchmark_name, input_type, data_stream):
        result_json = {}
        comp_dataset_name = "result"
        flag = 0
        for dataset_name, data in data_stream.items():
            json_res = self.extract_data(benchmark_name, dataset_name, input_type, data)
            if json_res["status"] != "success":
                return json_res

            if json_res["json_data"]:
                json_data = json_res["json_data"]
            if flag == 0:
                comp_dataset_name = dataset_name
                result_json = json_data
                flag = flag + 1
            else:
                comp_dataset_name = comp_dataset_name + "&" + dataset_name

                for i in json_data["data"]:
                    flag_test = 0
                    for j in result_json["data"]:
                        if (i["metrics_unit"] == j["metrics_unit"] and i["test_name"] == j["test_name"]):
                            j["instances"].extend(i["instances"])
                            flag_test = 1
                            continue

                    if (flag_test == 0):
                        result_json["data"].append(i)
        result_json["dataset_name"] = comp_dataset_name
        return {"status": "success", "json_data": result_json}

