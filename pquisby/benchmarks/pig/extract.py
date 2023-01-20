import re

from pquisby.pricing.cloud_pricing import get_cloud_cpu_count
from pquisby.util import read_config


def extract_pig_data(path, system_name,OS_RELEASE):
    results = []
    result_data = []
    cpu_count = 0
    region = read_config("cloud","region")
    cloud_type = read_config("cloud","cloud_type")
    # path = path + f"/iteration_1.{system_name}"
    with open(path) as file:
        for line in file:
            if "#" in line:
                header_row = line
            else:
                result_data.append(line.strip("\n").split(":"))
    
    cpu_count = get_cloud_cpu_count(
        system_name, region, cloud_type.lower()
    )
        # for line in file:
        #     if "PID" in line:
        #         cpu_data, thread_data = re.findall(r"(\w+\:\s\w+)", line)[1:3]
        #         efficiency = float(cpu_data.split()[1]) / float(thread_data.split()[1])
        #         result_data.append([thread_data.split()[1], efficiency])
        #     if not cpu_count:
        #         match = re.findall(r"(\w+\s\w+\s)(\d+)(\scpus)", line)
        #         if match:
        #             cpu_count = match[0][1]

    results.append([""])
    results.append([system_name, f"CpuCount: {cpu_count}"])
    results.append(["Threads", f"{OS_RELEASE}"])
    results += result_data

    return results
