import csv

from quisby.pricing import cloud_pricing
from quisby.benchmarks.linpack.extract import linpack_format_data


def extract_auto_hpl_data(path, system_name):

    if path.endswith(".csv"):
        with open(path) as file:
            results = []
            file_data = file.readlines()

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
                    return results

            else:
                return None

extract_auto_hpl_data("/Users/soumyasinha/Workspace/2022/rocky_rhel_gvnic/new_pull_aws/m5.metal/pbench-user-benchmark_dvalin_auto_hpl_test_2022.12.02T09.48.46/hpl-Intel_openblas-2022.12.02-09.48.57.csv","n2-standard-8")