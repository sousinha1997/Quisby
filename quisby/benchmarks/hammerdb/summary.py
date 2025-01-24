import re
from itertools import groupby
from quisby.util import mk_int, process_instance, read_config
from quisby import custom_logger
from quisby.pricing.cloud_pricing import get_cloud_pricing


def extract_prefix_and_number(input_string):
    """
    Extracts the prefix, number, and suffix from an input string.

    Args:
        input_string (str): The input string to extract parts from.

    Returns:
        tuple: (prefix, number, suffix) or (None, None, None) if no match is found.
    """
    match = re.search(r'^(.*?)(\d+)(.*?)$', input_string)
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)
        return prefix, number, suffix
    return None, None, None


def get_inst_name(item):
    """
    Extracts the instance name based on the cloud type.

    Args:
        item (str): The item (likely a cloud instance name) to process.

    Returns:
        str: The extracted instance name.
    """
    cloud_type = read_config("cloud", "cloud_type")
    if item == "local":
        return item
    elif cloud_type == "aws":
        return item.split("-")[0]
    elif cloud_type == "gcp":
        ll = item.split("-")
        return f"{ll[0]}-{ll[1]}-{ll[2]}"
    elif cloud_type == "azure":
        return item.split("-")[0]
    return item  # Return item if no known cloud type is found


def hammerdb_sort_data_by_system_family(results):
    """
    Sorts HammerDB results by system family and instance size.

    Args:
        results (list): A list of HammerDB results to sort.

    Returns:
        list: A sorted list of results.
    """
    sorted_results = []

    # Group results by non-empty rows and sort them
    results = [list(g) for k, g in groupby(results, key=lambda x: x != [""]) if k]
    results.sort(key=lambda x: str(process_instance(x[0][1], "family", "version", "feature")))

    # Group by family, then sort by size within each family
    for _, items in groupby(results, key=lambda x: process_instance(x[0][1], "family", "version", "feature")):
        items = list(items)
        sorted_results.append(sorted(items, key=lambda x: mk_int(process_instance(x[0][1], "size"))))

    return sorted_results


def calc_price_performance(inst, avg):
    """
    Calculates the price performance based on the instance and average.

    Args:
        inst (str): The instance type.
        avg (float): The average value to compute price performance.

    Returns:
        tuple: (cost per hour, price performance ratio).
    """
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")

    cost_per_hour = 0.0
    price_perf = 0.0
    try:
        cost_per_hour = get_cloud_pricing(inst, region, cloud_type.lower(), os_type)
        price_perf = float(avg) / float(cost_per_hour) if cost_per_hour > 0 else 0.0
    except Exception as exc:
        custom_logger.debug(f"Error in price calculation: {str(exc)}")
        custom_logger.error("Error calculating price performance!")
    return cost_per_hour, price_perf


def create_summary_hammerdb_data(hammerdb_data):
    """
    Creates a summary of the HammerDB data, including price-performance calculations.

    Args:
        hammerdb_data (list): A list of HammerDB data to summarize.

    Returns:
        list: A structured summary of the HammerDB data.
    """
    results = []

    # Sort the hammerdb data by system family
    hammerdb_data = hammerdb_sort_data_by_system_family(hammerdb_data)

    for data in hammerdb_data:
        run_data = {}
        price_per_perf = {}
        results.append([""])
        results.append([data[0][0][0]])  # System or family name

        price_results = [[""], ["Price-Perf"]]
        cost_per_hour = []

        for row in data:
            inst = get_inst_name(row[0][1])
            results[-1] += [row[0][1]]
            price_results[-1] += [row[0][1]]
            cph = 0.0
            pp = 0.0

            # Calculate price-performance for each data entry
            for ele in row[1:]:
                try:
                    cph, pp = calc_price_performance(inst, int(ele[1].strip()))
                except Exception as exc:
                    custom_logger.error(f"Error calculating price-performance: {str(exc)}")
                    cph = 0.0
                    pp = 0.0

                if ele[0] in run_data:
                    run_data[ele[0]].append(ele[1])
                else:
                    run_data[ele[0]] = [ele[1]]

                if ele[0] in price_per_perf:
                    price_per_perf[ele[0]].append(pp)
                else:
                    price_per_perf[ele[0]] = [pp]

            cost_per_hour.append([inst, cph])

        # Append run data results
        for key, item in run_data.items():
            results.append([key, *item])

        # Add cost per hour data
        results += [[""], ["Cost/Hr"]] + cost_per_hour

        # Add price-performance data
        results += price_results
        for key, item in price_per_perf.items():
            results.append([key, *item])

    return results
