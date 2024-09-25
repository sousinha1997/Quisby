from quisby.util import read_config


def extract_hammerdb_data(path, system_name, test_name, OS_RELEASE):
    results = []
    result_data = []
    summary_data = []
    summary_file = path
    server = read_config("server", "name")
    result_dir = read_config("server", "result_dir")

    data_index = 0
    header_row = []
    with open(path) as file:
        hammerdb_results = file.readlines()
        for index, line in enumerate(hammerdb_results):
            if "# connection:TPM" in line:
                data_index = index
                header_row = line.strip("\n").split(":")
            else:
                result_data.append(line.strip("\n").split(":"))
    result_data = result_data[data_index:]
    summary_data.append([system_name, server + "/results/" + result_dir + "/" + path])

    results.append([""])
    results.append([f"{test_name}-User Count",
                    f"{system_name}-{OS_RELEASE}"])
    results += result_data

    return results, summary_data
