from quisby import custom_logger

from quisby.pricing.cloud_pricing import get_cloud_cpu_count
from quisby.util import read_config


def extract_pig_data(path, system_name, OS_RELEASE):
    results = []
    result_data = []
    cpu_count = 0
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    # path = path + f"/iteration_1.{system_name}"
    try:
        with open(path) as file:
            for line in file:
                if "#" in line:
                    header_row = line
                else:
                    result_data.append(line.strip("\n").split(":"))
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
