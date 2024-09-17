import csv

from quisby.pricing import cloud_pricing
from quisby.benchmarks.linpack.extract import linpack_format_data

from quisby.util import read_config


def extract_auto_hpl_data(path, system_name):

    summary_data = []
    server = read_config("server", "name")
    result_dir = read_config("server", "result_dir")

    if path.endswith(".csv"):
        with open(path) as file:
            results = []
            file_data = file.readlines()
            sum_path = path.split("/./")[1]
            summary_data.append([system_name, "http://" + server + "/results/" + result_dir + "/" + sum_path])

            if len(file_data) > 1:
                header_row = file_data[-2].strip().split(":")
                data_row = file_data[-1].strip().split(":")

                data_dict = {}
                for key, value in zip(header_row, data_row):
                    data_dict[key] = value

                results = linpack_format_data(
                    results=results, system_name=system_name, gflops=data_dict["Gflops"]
                )

                if results:
                    return results, summary_data

            else:
                return None, None

