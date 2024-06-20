import csv
import glob
import os.path
import re

from quisby.pricing.cloud_pricing import get_cloud_pricing, get_cloud_cpu_count
from quisby.util import read_config


def linpack_format_data(**kwargs):
    """
    Add data into format to be shown in spreadsheets
    Supports linpack like data. eg: autohpl
    """
    region = read_config("cloud", "region")
    cloud_type = read_config("cloud", "cloud_type")
    os_release = read_config("test", "OS_RELEASE")
    os_type = read_config("test", "os_type")
    results = kwargs["results"] if kwargs["results"] else []
    system_name = kwargs["system_name"] if kwargs["system_name"] else None
    if kwargs["gflops"]:
        gflops = float(kwargs["gflops"])
    else:
        return None

    price_per_hour = get_cloud_pricing(
        system_name, region, cloud_type.lower(), os_type
    )

    no_of_cores = get_cloud_cpu_count(
        system_name, region, cloud_type.lower()
    )

    results.append(
        [
            "System",
            "Cores",
            f"GFLOPS-{os_release}",
            f"GFLOP Scaling-{os_release}",
            "Cost/hr",
            f"Price/Perf-{os_release}",
        ]
    )
    results.append(
        [
            system_name,
            no_of_cores,
            gflops,
            1,
            price_per_hour,
            float(gflops) / float(price_per_hour),
        ]
    )

    return results


def extract_linpack_data(path, system_name):
    """
    Make shift function to handle linpack summary data
    till a resolution is reached
    """

    results = []
    no_of_cores = None
    gflops = None

    summary_file = path

    if not os.path.isfile(summary_file):
        return None

    if os.path.basename(summary_file).endswith("csv"):
        with open(summary_file) as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=":")
            list_data = list(csv_reader)
            last_row = list_data[-1]
            gflops = last_row["MB/sec"]
            threads = last_row["threads"]
    else:
        return results

    for file_path in glob.glob(path + f"/linpack*_threads_{threads}_*"):
        with open(file_path) as txt_file:
            data = txt_file.readlines()
            for row in data:
                if re.findall(r"Number of cores: (\d+)", row):
                    no_of_cores = re.findall(r"Number of cores: (\d+)", row)[0]
                    break

    if gflops:
        results = linpack_format_data(
            results=results,
            system_name=system_name,
            no_of_cores=no_of_cores,
            gflops=gflops,
        )

        return results
