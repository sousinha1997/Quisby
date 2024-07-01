from scipy.stats import gmean

from quisby import custom_logger
from quisby.util import read_config
from quisby.pricing.cloud_pricing import get_cloud_pricing

def custom_key(item):
    cloud_type = read_config("cloud", "cloud_type")
    if item[0] == "localhost":
        return item[0]
    elif cloud_type == "aws":
        instance_type = item[0].split(".")[0]
        instance_number = item[0].split(".")[1]
        return instance_type, instance_number
    elif cloud_type == "gcp":
        instance_type = item[0].split("-")[0]
        instance_number = int(item[0].split('-')[-1])
        return instance_type, instance_number


def calc_price_performance(inst, avg):
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")
    cost_per_hour = None
    try:
        cost_per_hour = get_cloud_pricing(
            inst, region, cloud_type.lower(), os_type)
        price_perf = float(avg / pow(10,3))/float(cost_per_hour)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Error calculating value !")
    return cost_per_hour, price_perf


def create_summary_passmark_data(data, OS_RELEASE):
    results = [
        ['SYSTEM', "NO_OF_TEST_PROCESSES", "CPU_INTEGER_MATH", "CPU_FLOATINGPOINT_MATH", "CPU_PRIME", "CPU_SORTING",
         "CPU_ENCRYPTION", "CPU_COMPRESSION", "CPU_SINGLETHREAD", "CPU_PHYSICS", "CPU_MATRIX_MULT_SSE", "CPU_mm",
         "CPU_sse", "CPU_fma", "CPU_avx", "CPU_avx512", "m_CPU_enc_SHA", "m_CPU_enc_AES", "m_CPU_enc_ECDSA",
         "ME_ALLOC_S", "ME_READ_S", "ME_READ_L", "ME_WRITE", "ME_LARGE", "ME_LATENCY", "ME_THREADED", "SUMM_CPU",
         "SUMM_ME"
         ]]
    processed_data = None
    gmean_data = []
    SYSTEM_GEOMEAN = []
    end_index = 0
    start_index = 0
    system = ""
    cost_per_hour, price_per_perf = [], []
    # Add summary data
    for index, row in enumerate(data):
        if row == [""]:
            if processed_data:
                inst = processed_data[0]
                results.append(processed_data)
                gdata = gmean(gmean_data)
                SYSTEM_GEOMEAN.append([system, gdata])
                try:
                    cph, pp = calc_price_performance(inst, gdata)
                except Exception as exc:
                    custom_logger.error(str(exc))
                    continue
                if not pp:
                    price_per_perf.append([inst, 0.0])
                else:
                    price_per_perf.append([inst, 1.0 / pp])

                cost_per_hour.append([inst, cph])

            processed_data = []
            gmean_data = []
            system = ""
            start_index = end_index + 1
            end_index = 0
        elif start_index:
            system = row[0]
            processed_data.append(system)
            end_index = start_index + 1
            start_index = 0
        elif end_index:
            if not row[0] == 'NumTestProcesses':
                gmean_data.append(float(row[1]))
            processed_data.append(row[1])

    if processed_data:
        cph = 0
        pp = 0
        inst = processed_data[0]
        results.append(processed_data)
        gdata = gmean(gmean_data)
        SYSTEM_GEOMEAN.append([system, gdata])
        try:
            cph, pp = calc_price_performance(inst, gdata)
        except Exception as exc:
            custom_logger.error(str(exc))
        if not pp:
            price_per_perf.append([inst, pp])
        else:
            price_per_perf.append([inst, 1.0 / pp])
        cost_per_hour.append([inst, cph])

    results.append([""])
    results.append(["SYSTEM_NAME", "GEOMEAN-" + str(OS_RELEASE)])
    sorted_data = sorted(SYSTEM_GEOMEAN, key=custom_key)
    for item in sorted_data:
        results.append(item)
    results.append([""])
    results.append(["Cost/Hr"])
    sorted_data = sorted(cost_per_hour, key=custom_key)
    for item in sorted_data:
        results.append(item)
    results.append([""])
    results.append(["SYSTEM_NAME", f"Price/perf-{OS_RELEASE}"])
    sorted_data = sorted(price_per_perf, key=custom_key)
    for item in sorted_data:
        results.append(item)
    return results


def extract_passmark_data(path, system_name, OS_RELEASE):
    """"""
    results = []
    # Extract data from file
    try:
        if path.endswith("results.csv"):
            with open(path) as file:
                coremark_results = file.readlines()
        else:
            return None
    except Exception as exc:
        custom_logger.error(str(exc))
        return None

    for index, data in enumerate(coremark_results):
        coremark_results[index] = data.strip("\n").split(":")
    results.append([""])
    results.append([system_name])
    results.extend(coremark_results)
    return results
