from quisby import custom_logger

from quisby.pricing.cloud_pricing import get_cloud_cpu_count
from quisby.util import read_config


def extract_pig_data(path, system_name, OS_RELEASE):
    results = []
    result_data = []
    cpu_count = 0
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")

    data_index = 0

    try:
        with open(path) as file:
            pig_results = file.readlines()
            for index, data in enumerate(pig_results):
                if "#threads sched_eff" in data:
                    data_index = index
                    header = data.strip("\n")
                else:
                    result_data.append(data.strip("\n").split(":"))
            result_data = result_data[data_index :]
    except Exception as exc:
        custom_logger.error(str(exc))
        return None

    cpu_count = get_cloud_cpu_count(
        system_name, region, cloud_type.lower()
    )

    results.append([""])
    results.append([system_name, f"CpuCount: {cpu_count}"])
    results.append(["Threads", "rhel-" + f"{OS_RELEASE}"])
    results += result_data

    return results

