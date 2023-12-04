import re
import logging
from itertools import groupby
import requests
from bs4 import BeautifulSoup


# TODO: Maybe we can do away with clat, lat, slat
HEADER_TO_EXTRACT = [
    "iops_sec:client_hostname:all",
    "lat:client_hostname:all",
]


def extract_csv_data(csv_data, path):
    logging.info("Extracting required data...")
    indexof_all = []
    results = []
    header_row = csv_data.pop(0)
    if path == "":
        io_depth = "<>"
        ndisks = "<>"
        njobs = "<>"

    else:
        io_depth = re.findall(r"iod.*?_(\d+)", path)[0]
        ndisks = re.findall(r"ndisks_(\d+)", path)[0]
        njobs = re.findall(r"njobs_(\d+)", path)[0]

    logging.info("IO_DEPTH: "+io_depth+" | NDISKS: "+ndisks+" | NJOBS: "+njobs)

    for header in HEADER_TO_EXTRACT:
        for name in header_row:
            if name.startswith(header):
                indexof_all.append(header_row.index(name))
    if not indexof_all:
        logging.warning("No data found to push. Exiting...")
        raise ValueError

    try:
        for row in csv_data:
            logging.debug(row)
            run_data = []
            if row:
                try:
                    csv_row = row
                    for index in indexof_all:
                        run_data.append(csv_row[index])
                    results.append([csv_row[1], ndisks, njobs, io_depth, *run_data])
                except Exception as exc:
                    logging.warning("Invalid row data. Ignoring...")
    except Exception as exc:
        logging.error("Data format incorrect. Skipping data")
        raise exc

    if results == []:
        logging.warning("Found empty values. Please check the logs for details...")

    return results


def group_data(run_data, json_data, dataset_name, OS_RELEASE):

    """ Groups data into similar metric groups
        Parameters
        ----------
        run_data : list
            Extracted raw data from results location
        system_name : str
            Machine name
        OS_RELEASE : str
            Release version of machine"""
    logging.info("Grouping data to a specified format")
    run_metric = {"1024KiB": ["iops", "lat"], "4KiB": ["lat", "iops"]}
    json_data["dataset_name"] = dataset_name
    json_data["data"] = []
    grouped_data = []
    count = 1
    for key, items in groupby(sorted(run_data), key=lambda x: x[0].split("-")):
        for item in items:
            for value in run_metric[key[1]]:
                item_json = {}
                item_json["vm_name"] = ""
                item_json["test_name"] =  key[0]
                item_json["metrics_unit"] = f"{key[1]}-{value}"
                item_json["instances"] = []
                test_json = {}
                grouped_data.append([""])
                grouped_data.append(["", key[0], f"{key[1]}-{value}"])
                grouped_data.append(["iteration_name", f"{value}-{OS_RELEASE}"])
                row_hash = f"{item[1]}_d-{item[2]}_j-{item[3]}_iod"
                test_json["iteration_name"] = count
                test_json["dataset_name"] = dataset_name
                if "iops" in value:
                    grouped_data.append([row_hash, item[4].strip()])
                    test_json["value"] = item[4].strip()
                elif "lat" in value:
                    grouped_data.append([row_hash, item[5].strip()])
                    test_json["value"] = item[5].strip()
                item_json["instances"].append(test_json)
                json_data["data"].append(item_json)
        count = count + 1


    if grouped_data == [] or json_data == {"dataset_name": "", "data": [], }:
        logging.warning("Found empty values. Please check the logs for details...")
        raise ValueError

    logging.info(grouped_data)
    logging.info(json_data)
    return grouped_data, json_data


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


def extract_fio_run_data(dataset_name, csv_data, path):
    """Extracts raw data from results location and groups into a specific format
            Parameters
            ----------
            path : str
                Path to results csv file
            dataset_name : str
                Dataset name
            csv_data : str
                raw data"""
    try:
        result_json = {
            "dataset_name": "",
            "data": [],
        }

        results = extract_csv_data(csv_data, path)
        return group_data(results, result_json, dataset_name, "9")
    except Exception as exc:
        logging.error("Failed to fetch FIO data...")
        raise exc
    return [], {}

