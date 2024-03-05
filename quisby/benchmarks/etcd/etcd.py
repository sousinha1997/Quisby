import os

from quisby.benchmarks.fio.fio import extract_fio_run_data, extract_csv_data, group_data
from quisby.benchmarks.fio.summary import create_summary_fio_run_data
from quisby.benchmarks.fio.graph import graph_fio_run_data
from quisby.benchmarks.fio.comparison import compare_fio_run_results


def extract_etcd_data(path, system_name):
    results = []

    ls_dir = os.listdir(path)

    for folder in ls_dir:
        with open(path + f"/{folder}/result_etcd.csv") as csv_file:
            csv_data = csv_file.readlines()
            csv_data[-1] = csv_data[-1].strip()

            results += extract_csv_data(csv_data, folder)

    return group_data(results, system_name)


def create_summary_etcd_data(results):
    return create_summary_fio_run_data(results)


def graph_etcd_data(spreadsheetId, test_name, action):
    return graph_fio_run_data(spreadsheetId, test_name, action)


def compare_etcd_results(spreadsheets, spreadsheetId, test_name):
    return compare_fio_run_results(spreadsheets, spreadsheetId, test_name)
