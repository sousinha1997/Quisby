from itertools import groupby
import re
from quisby import custom_logger
from quisby.util import mk_int, process_instance,read_config


def extract_prefix_and_number(input_string):
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)
        return prefix, number, suffix
    return None, None, None


def custom_key(item):
    cloud_type = read_config("cloud","cloud_type")
    if item[0][0] == "local":
        return item[0][0]
    elif cloud_type == "aws":
        instance_type =item[0][0].split(".")[0]
        instance_number = item[0][0].split(".")[1]
        return instance_type, instance_number
    elif cloud_type == "gcp":
         instance_type = item[0][0].split("-")[0]
         instance_number = int(item[0][0].split('-')[-1])
         return instance_type, instance_number
    elif cloud_type == "azure":
        instance_type, instance_number, version=extract_prefix_and_number(item[0][0])
        return instance_type, version, instance_number


def fio_run_sort_data(results):
    """Sort FIO run data by specific conditions such as instance family, size, and operation type."""
    sorted_result = []

    # Group results by non-empty entries
    results = [list(g) for k, g in groupby(results, key=lambda x: x != [""]) if k]

    # Sort results by operation type and size
    results.sort(key=lambda x: (
        x[0][1],  # Operation type (read/write)
        x[0][2],  # Size
        str(process_instance(x[0][0], "family", "version", "feature"))  # Instance details
    ))

    # Group by family, operation type, and size, then sort within each group by size
    for _, items in groupby(results, key=lambda x: (
            process_instance(x[0][0], "family", "version", "feature"),
            x[0][1],  # Operation type
            x[0][2]  # Size
    )):
        sorted_result += sorted(list(items), key=lambda x: mk_int(process_instance(x[0][1], "size")))

    return sorted_result


def key_func(sublist):
    parts = sublist[0].split('_')
    d_num = int(parts[0])
    j_num = int(parts[1].split("-")[1])
    iod_num = int(parts[2].split("-")[1])
    return d_num, j_num, iod_num, float(sublist[1])


def create_summary_fio_run_data(results, OS_RELEASE):
    """ Create summary of the extracted raw data
        Parameters
        ----------
        results : list
            Extracted raw data from results location"""
    summary_results = []
    sort_result_disk = []
    try:
        results = fio_run_sort_data(results)
    except Exception as exc:
        custom_logger.error(str(exc))
    sorted_data = sorted(results, key=custom_key)
    for header, items in groupby(sorted_data, key=lambda x: [x[0][0], x[0][1], x[0][2]]):
        try:
            items = list(items)
            summary_results.append([""])
            summary_results.append([header[0], header[1], header[2]])
            summary_results.append(["iteration_name", items[0][1][1]])
            for index, item in enumerate(items):
                # Add individual data tables
                sort_result_disk.append(item[2])
            summary_results.extend(sorted(sort_result_disk, key=key_func))
            sort_result_disk = []

        except Exception as exc:
            custom_logger.error(str(exc))
            pass
    return summary_results
