
""" Custom key to sort the data base don instance name """
from quisby import custom_logger


from quisby.util import read_config

def custom_key(item):
    cloud_type = read_config("cloud","cloud_type")
    if item[1][0] == "localhost":
        return (item[1][0])
    elif cloud_type == "aws":
        instance_type =item[1][0].split(".")[0]
        instance_number = item[1][0].split(".")[1]
        return (instance_type, instance_number)
    elif cloud_type == "gcp":
         instance_type = item[1][0].split("-")[0]
         instance_number = int(item[1][0].split('-')[-1])
         return (instance_type, instance_number)
    elif cloud_type == "azure":
        instance_type = item[1][0].split("_")[0]
        instance_number = item[1][0].split("_")[1]+item[1][0].split("_")[2]
        return (instance_type, instance_number)

def create_summary_coremark_data(results,OS_RELEASE):
    final_results = []
    cal_data = [["System name","test passes"]]

    # Sort data based on instance name
    sorted_data = sorted(results, key=custom_key)

    # Add summary data
    for item in sorted_data:
        sum = 0
        avg = 0
        iterations = 0
        for index in range(3,len(item)):
            sum = sum + float(item[index][1])
            iterations = iterations + 1
        avg = float(sum/iterations)
        cal_data.append([item[1][0],avg])

        final_results += item
    final_results += [[""]]
    final_results += cal_data
    return final_results

def extract_coremark_data(path, system_name, OS_RELEASE):
    """"""
    results = []
    processed_data =[]

    # Extract data from file
    try:
        if path.endswith(".csv"):
            with open(path) as file:
                coremark_results = file.readlines()
        else:
            return None
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Unable to extract data from csv file for coremark")
        return None

    for index, data in enumerate(coremark_results):
        coremark_results[index] = data.strip("\n").split(":")

    # Format the data
    iteration = 1
    for row in coremark_results:
        if "test passes" in row:
            processed_data.append([""])
            processed_data.append([system_name])
            processed_data.append([row[0], row[2]])
        else:
            processed_data.append([iteration, row[2]])
            iteration = iteration + 1
    results.append(processed_data)

    return results

results = []
ret_val = extract_coremark_data("/Users/soumyasinha/Workspace/2024/Quisby/quisby/benchmarks/coremark/results.csv","Standard_D16as_v5","9.3")
if ret_val:
    results += ret_val
create_summary_coremark_data(results,"9.3")

