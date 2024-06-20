

def extract_hammerdb_data(path, system_name, test_name, OS_RELEASE):
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
