import csv

from quisby import custom_logger


def process_speccpu(path, system_name, suite, OS_RELEASE):
    results = []

    with open(path) as csv_file:
        speccpu_results = list(csv.DictReader(csv_file, delimiter=":"))

    results.append([""])
    results.append([system_name, suite])
    results.append(["Benchmark", f"Base_Rate-{OS_RELEASE}"])
    for data_row in speccpu_results:
        try:
            results.append([data_row['Benchmarks'], data_row['Base Rate']])
        except Exception as exc:
            custom_logger.debug(str(exc))
            pass
    return results


def extract_speccpu_data(path, system_name, OS_RELEASE):
    results = []

    if "fprate" in path:
        results += process_speccpu(path, system_name, "fprate", OS_RELEASE)
    elif "intrate" in path:
        results += process_speccpu(path, system_name, "intrate", OS_RELEASE)

    return results
