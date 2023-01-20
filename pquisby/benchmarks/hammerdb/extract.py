import re

# def extract_hammerdb_data(path_list, system_name, test_name):
#     results = []
#     run_data = []

#     for path in path_list:
#         warehouse_count = re.findall(r"(_)(\d+)(.out)", path)[0][1]
#         with open(path) as hdb_out_file:
#             hdb_run_output = hdb_out_file.readlines()

#             for line in hdb_run_output:
#                 match_list = re.findall(r"(System\sachieved\s)(\d+)", line)
#                 if match_list:
#                     run_data.append([warehouse_count, match_list[0][1]])

#     run_data.sort(key=lambda x: int(x[0]))

#     results.append([f"{test_name}-User count", f"{system_name}-{config.OS_RELEASE}"])
#     results += run_data

#     return results

def extract_hammerdb_data(path, system_name, test_name,OS_RELEASE):
    results = []
    result_data = []

    with open(path) as file:
        for line in file:
            if "#" in line:
                header_row = line.split(":")
            else:
                result_data.append(line.strip("\n").split(":"))

    results.append([""])
    results.append([f"{test_name}-User Count",
                   f"{system_name}-{OS_RELEASE}"])
    results += result_data

    return results
