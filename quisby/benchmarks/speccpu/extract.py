import csv

from quisby import custom_logger

from quisby.util import read_config


def process_speccpu(path, system_name, suite, OS_RELEASE):
    results = []
    summary_data = []
    server = read_config("server", "name")
    result_dir = read_config("server", "result_dir")

    with open(path) as csv_file:
        speccpu_results = list(csv.DictReader(csv_file, delimiter=":"))
        summary_data.append([system_name, server + "/results/" + result_dir + "/" + path])

    results.append([""])
    results.append([system_name, suite])
    results.append(["Benchmark", f"Base_Rate-{OS_RELEASE}"])
    for data_row in speccpu_results:
        try:
            results.append([data_row['Benchmarks'], data_row['Base Rate']])
        except Exception as exc:
            custom_logger.debug(str(exc))
            pass
    return results,summary_data


def extract_speccpu_data(path, system_name, OS_RELEASE):
    results = []
    summary_data = []
    if "fprate" in path:
        fp_results, fp_summary_data= process_speccpu(path, system_name, "fprate", OS_RELEASE)
        results +=fp_results
        summary_data += fp_summary_data
    elif "intrate" in path:
        int_results, int_summary_data= process_speccpu(path, system_name, "intrate", OS_RELEASE)
        results +=int_results
        summary_data +=int_summary_data

    return results, summary_data
