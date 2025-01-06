import os
from itertools import groupby

from quisby.util import mk_int, process_instance

from quisby import custom_logger
from quisby.pricing.cloud_pricing import get_cloud_pricing
from quisby.util import read_config


def stream_sort_data_by_system_family(results):
    """"""
    stream_data = []
    sorted_result = []

    for index in range(0, len(results), 7):
        stream_data.append(results[index: index + 7])

    stream_data.sort(
        key=lambda x: str(process_instance(x[2][0], "family", "version", "feature"))
    )

    for _, items in groupby(
            stream_data,
            key=lambda x: process_instance(x[2][0], "family", "version", "feature"),
    ):
        sorted_result.append(
            sorted(list(items), key=lambda x: mk_int(process_instance(x[2][0], "size")))
        )

    return sorted_result


def calc_max_throughput(data):
    """"""
    num_of_socket = data[1][0].split(" ")[0]
    system_name = data[2][0]
    cph = []
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_type = read_config("test", "os_type")
    system_price = 1
    try:
        system_price = get_cloud_pricing(
            system_name, region, cloud_type.lower(), os_type)
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Error calculating value !")
        system_price = 0.0

    max_copy = max(data[3][1:])
    max_price_copy = float(max_copy)/ system_price
    max_scale = max(data[4][1:])
    max_price_scale = float(max_scale) / system_price
    max_add = max(data[5][1:])
    max_price_add = float(max_add) / system_price
    max_triad = max(data[6][1:])
    max_price_triad = float(max_triad) / system_price
    cph.append([system_name, system_price])

    return ([
        system_name + " Sockets:" + num_of_socket,
        max_copy,
        max_scale,
        max_add,
        max_triad,
    ], [
        system_name + " Sockets:" + num_of_socket,
        max_price_copy,
        max_price_scale,
        max_price_add,
        max_price_triad,
    ], cph)


def create_summary_streams_data(stream_data, OS_RELEASE):
    """
    Create summary data for Max throughput and Scaling
    """
    results = []

    stream_data = stream_sort_data_by_system_family(stream_data)

    # Group by system family
    for items in stream_data:
        max_calc_result = []
        price_result = []
        cost_list = [["Cost/Hr"]]
        for item in items:
            cost_per_hr = []
            results += item
            res_calc = calc_max_throughput(item)
            max_calc, price, cost_per_hr = res_calc[0], res_calc[1], res_calc[2]
            max_calc_result.append(max_calc)
            price_result.append(price)
            cost_list +=cost_per_hr
        results.append([""])
        results.append(
            [
                "Max Throughput",
                f"Copy-{OS_RELEASE}",
                f"Scale-{OS_RELEASE}",
                f"Add-{OS_RELEASE}",
                f"Triad-{OS_RELEASE}",
            ]
        )

        results += max_calc_result
        results.append([""])
        results += cost_list
        results.append([""])
        results.append(
            [
                "Price-Perf",
                f"Thrpt-copy/$-{OS_RELEASE}",
                f"Thrpt-scale/$-{OS_RELEASE}",
                f"Thrpt-add/$-{OS_RELEASE}",
                f"Thrpt-triad/$-{OS_RELEASE}",
            ]
        )

        results += price_result
    return results


def extract_streams_data(path, system_name, OS_RELEASE):
    """
    Extracts streams data and appends empty list for each seperate stream runs

    :path: stream summary results file from stream_wrapper_benchmark runs
    :system_name: machine name (eg: m5.2xlarge, Standard_D64s_v3)
    """

    summary_data = []
    summary_file = path


    if not os.path.isfile(summary_file):
        return None

    with open(path) as file:
        streams_results = file.readlines()


    data_index = 0
    for index, data in enumerate(streams_results):
        if "buffer size" in data:
            data_index = index
        streams_results[index] = data.strip("\n").split(":")

    # streams_results = sorted(streams_results[data_index + 1 :], key=lambda x: x[2])

    socket_number = ""
    proccessed_data = []
    length = len(streams_results)
    pos = 7
    memory = ""
    if not streams_results:
        return None
    for i in range(0, length):
        row = streams_results[i]
        if "memory" in row[0]:
            memory = row[0].split(" ")[-1]
        elif " Socket" in row[0] and "% Socket" not in row[0]:
            socket_number = row[0].split(" ")[0]
            proccessed_data += (
                [""],
                [f"{socket_number} socket"],
                [system_name],
                ["copy"],
                ["scale"],
                ["add"],
                ["triad"],
            )
            pos = len(proccessed_data)
        elif row == [""]:
            pass
        elif row[0] in ("Copy", "Scale", "Add", "Triad"):

            if row[0] == "Copy":
                data_pos = pos - 4
            if row[0] == "Scale":
                data_pos = pos - 3
            if row[0] == "Add":
                data_pos = pos - 2
            if row[0] == "Triad":
                data_pos = pos - 1
            proccessed_data[pos - 5].append(memory + "-" + OS_RELEASE)
            proccessed_data[data_pos].extend(row[1:])
    return proccessed_data


if __name__ == "__main__":
    extract_streams_data(
        "results_streams.csv",
        "i3en.xlarge",
    )
