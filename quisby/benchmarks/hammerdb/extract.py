
def extract_hammerdb_data(path, system_name, test_name, OS_RELEASE):
    """
    Extracts HammerDB results from a file and processes them into a structured format.

    Args:
        path (str): The path to the HammerDB result file.
        system_name (str): The name of the system.
        test_name (str): The name of the test.
        os_release (str): The OS release version.

    Returns:
        list: A list containing processed HammerDB data.
    """
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
