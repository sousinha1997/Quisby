import fileinput
import logging
from email.policy import default
import click
from pquisby.lib.benchmarks.uperf.uperf import extract_uperf_data
from pquisby.lib.process_result import process_results

@click.command()
@click.option('--run-name', help='Run name')
@click.option('--results-location', help="File path for results")
@click.option('--os-version', help="Distro and version")
@click.option('--controller-name', help="Controller Name")
@click.option('--spreadsheet_id', help="Any specific spreadsheet")
@click.option('--spreadsheet_name', help="Any specific spreadsheet name")
def single_run(run_name, results_location, os_version, controller_name,spreadsheet_id,spreadsheet_name):

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
                    path = data.split(",")[0]
                    if test_name == "uperf":
                        ret_val = extract_uperf_data(path, controller_name)
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
        print(f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


        



    
                