import os
import re
from itertools import groupby

import requests
from bs4 import BeautifulSoup

from quisby import custom_logger
from quisby.util import read_config

# TODO: Maybe we can do away with clat, lat, slat
HEADER_TO_EXTRACT = [
    "iops_sec:client_hostname:all",
    "lat:client_hostname:all",
]

def split_into_parts(data):
    result = []
    temp = []

    # Iterate through the data
    for item in data:
        if item == "\n":
            if temp:
                result.append(temp)
                temp = []
        else:
            temp.append(item)

    # Append the last group if it's not empty
    if temp:
        result.append(temp)
    return result

def extract_csv_data(csv_data):
    indexof_all = []
    result = []
    op_value = ""
    size_value = ""
    metric = ""
    for i, line in enumerate(csv_data):
        if line.startswith('# op:'):
            op_value = line.split(':')[1].strip()
        elif line.startswith('# size:'):
            size_value = line.split(':')[1].strip()
        if line.startswith('njobs:ndisks:iodepth:'):
            metric = line.split(":")[-1].strip()
            header_line_index = i
            break

    data_lines = csv_data[header_line_index + 1:]

    try:
        for line in data_lines:
            # Split the values in the format '1:1:1:641169.83'
            values = line.split(":")
            if len(values) == 4:  # If the line contains the expected format
                njobs, ndisks, iodepth, value = values
                result.append([f"{op_value}-{size_value}", int(njobs), int(ndisks), int(iodepth), f" {value}", metric])
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.error("Data format incorrect. Skipping data")
    return result


def group_data(run_data, system_name, OS_RELEASE):
    """ Groups data into similar metric groups
        Parameters
        ----------
        run_data : list
            Extracted raw data from results location
        system_name : str
            Machine name
        OS_RELEASE : str
            Release version of machine"""
    run_metric = {"1024KiB": ["iops", "lat"], "4KiB": ["lat", "iops"]}
    grouped_data = []
    for key, items in groupby(sorted(run_data), key=lambda x: x[0].split("-")):
        for item in items:
            grouped_data.append([""])
            grouped_data.append([system_name, key[0], f"{key[1]}-{item[5]}"])
            grouped_data.append(["iteration_name", f"{item[5]}-{OS_RELEASE}"])
            row_hash = f"{item[1]}_d-{item[2]}_j-{item[3]}_iod"
            grouped_data.append([row_hash, item[4]])
    return grouped_data


# TODO: parellelize work
def retreive_data_from_url(URL, page_content):
    results = []

    if page_content:

        for link in page_content[3:]:

            path = link.text.split("/")[0]

            if path:
                csv_data = requests.get(URL + path + "/result.csv")

                results += extract_csv_data(csv_data.text.split("\n"), path)

    return results


def scrape_page(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    page_content = soup.table.find_all("tr")

    return page_content


def get_system_name_from_url(URL):
    return re.findall(r"instance_(\w+.\w+)_numb", URL)[0]


def process_fio_run_result(URL, system_name):
    # system_name = get_system_name_from_url(URL)
    page_content = scrape_page(URL)
    results = retreive_data_from_url(URL, page_content)

    return group_data(results, system_name)


def extract_fio_run_data(path, system_name, OS_RELEASE):
    """Extracts raw data from results location and groups into a specific format
            Parameters
            ----------
            path : str
                Path to results csv file
            system_name : str
                Machine name
            OS_RELEASE : str
                Release version of machine"""
    results = []
    summary_data = []
    summary_file = path


    try:
        with open(path) as csv_file:
            csv_data = csv_file.readlines()
            csv_data = split_into_parts(csv_data)
            for data in csv_data:
                results += extract_csv_data(data)

        return group_data(results, system_name, OS_RELEASE)
    except Exception as exc:
        custom_logger.error("Unable to find fio path")
        custom_logger.error(str(exc))

    return []
