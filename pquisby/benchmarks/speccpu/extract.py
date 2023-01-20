import glob
import csv

# def process_speccpu(path, system_name, suite):
#     results = []
#     suite_path = glob.glob(f"{path}/*{suite}.refrate.results.csv")[0]

#     with open(suite_path) as file:
#         speccpu_results = file.readlines()

#     start_index, end_index = 0, 0
#     for index, row in enumerate(speccpu_results):

#         if "Full Results Table" in row:
#             start_index = index + 2

#         if start_index:
#             if "Selected Results Table" in row:
#                 end_index = index - 1
#                 break

#     results.append([""])
#     results.append([system_name, suite])
#     for index, row in enumerate(speccpu_results[start_index:end_index]):
#         row = row.split(",")
#         if index == 0:
#             results.append([row[0], f"Base_Rate-{config.OS_RELEASE}"])
#         else:
#             results.append([row[0], f"{row[3]}"])

#     return results

def process_speccpu(path, system_name, suite,OS_RELEASE):
    results = []
    suite_path = glob.glob(f"{path}/*{suite}.refrate.results.csv")[0]

    with open(suite_path) as csv_file:
        speccpu_results = list(csv.DictReader(csv_file, delimiter=":"))

    results.append([""])
    results.append([system_name, suite])
    results.append(["Benchmark", f"Base_Rate-{OS_RELEASE}"])
    for data_row in speccpu_results:
        results.append([data_row['Benchmarks'], data_row['Base Rate']])
    print(results)
    return results
    

def extract_speccpu_data(path, system_name,OS_RELEASE):
    results = []

    for suite in ["fprate", "intrate"]:
        results += process_speccpu(path, system_name, suite,OS_RELEASE)

    return results
