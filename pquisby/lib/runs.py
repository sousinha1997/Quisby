import fileinput
import logging
import os.path

from pquisby.lib.benchmarks.uperf.uperf import extract_uperf_data
from pquisby.lib.process_result import process_results


def data_handler(run_name, results_location, os_version, controller_name,spreadsheet_id,spreadsheet_name):
    results = []
    if not spreadsheet_name:
        spreadsheet_name = run_name
    if not spreadsheet_id:
        spreadsheet_id = ""

    for line in fileinput.FileInput(results_location, inplace=1):
        if line.rstrip():
            print(line, end="")

    with open(results_location) as file:
        test_result_path = file.readlines()

        for data in test_result_path:
            if "test: " in data:
                if results:
                    spreadsheet_id = process_results(results, test_name, os_version, spreadsheet_name, spreadsheet_id)
                results = []
                test_name = data.replace("test: ", "").strip()
            else:
                try:
                    csv_path = data.split(",")[0]
                    test_path = results_location.strip("results_location")
                    if test_name == "uperf":
                        ret_val,json_data = extract_uperf_data(controller_name, os.path.join(test_path, csv_path))
                        if ret_val:
                            results += ret_val
                        else:
                            return None
                    else:
                        continue
                except ValueError as exc:
                    logging.error(str(exc))
                    continue
        try:
            spreadsheet_id = process_results(results, test_name, os_version, spreadsheet_name,spreadsheet_id)
        except Exception as exc:
            logging.error(str(exc))
            pass
        return spreadsheet_id


