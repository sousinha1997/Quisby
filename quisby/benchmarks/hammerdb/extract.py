
def extract_hammerdb_data(path, system_name, test_name, OS_RELEASE):
    results = []
    result_data = []
    data_index = 0
    with open(path) as file:
        hammerdb_results = file.readlines()
        for index, line in enumerate(hammerdb_results):
            if "# connection:TPM" in line:
                data_index = index
            else:
                result_data.append(line.strip("\n").split(":"))
    result_data = result_data[data_index:]

    results.append([""])
    results.append([f"{test_name}-User Count",
                    f"{system_name}-{OS_RELEASE}"])
    results += result_data

    return results
