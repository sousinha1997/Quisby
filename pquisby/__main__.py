import os.path
import sys
import glob
import argparse
import fileinput
import time
import logging
from pquisby.sheet.sheetapi import sheet
from pquisby.sheet.sheet_util import (
    get_sheet,
    create_sheet,
    append_to_sheet,
    create_spreadsheet,
)
from pquisby.benchmarks.streams.streams import (
    extract_streams_data,
    create_summary_streams_data,
)
from pquisby.benchmarks.streams.graph import graph_streams_data
from pquisby.benchmarks.streams.comparison import compare_streams_results
from pquisby.benchmarks.uperf.uperf import extract_uperf_data, create_summary_uperf_data
from pquisby.benchmarks.uperf.graph import graph_uperf_data
from pquisby.benchmarks.uperf.comparison import compare_uperf_results
from pquisby.benchmarks.specjbb.specjbb import (
    extract_specjbb_data,
    create_summary_specjbb_data,
)
from pquisby.benchmarks.specjbb.comparison import compare_specjbb_results
from pquisby.benchmarks.specjbb.graph import graph_specjbb_data
from pquisby.benchmarks.pig.extract import extract_pig_data
from pquisby.benchmarks.pig.graph import graph_pig_data
from pquisby.benchmarks.pig.summary import create_summary_pig_data
from pquisby.benchmarks.pig.comparison import compare_pig_results
from pquisby.benchmarks.linpack.extract import extract_linpack_data
from pquisby.benchmarks.linpack.summary import create_summary_linpack_data
from pquisby.benchmarks.linpack.graph import graph_linpack_data
from pquisby.benchmarks.linpack.comparison import compare_linpack_results
from pquisby.benchmarks.hammerdb.extract import extract_hammerdb_data
from pquisby.benchmarks.hammerdb.summary import create_summary_hammerdb_data
from pquisby.benchmarks.hammerdb.graph import graph_hammerdb_data
from pquisby.benchmarks.hammerdb.comparison import compare_hammerdb_results
from pquisby.benchmarks.fio.fio import process_fio_run_result, extract_fio_run_data
from pquisby.benchmarks.fio.summary import create_summary_fio_run_data
from pquisby.benchmarks.fio.graph import graph_fio_run_data
from pquisby.benchmarks.fio.comparison import compare_fio_run_results
from pquisby.benchmarks.aim.extract import extract_aim_data
from pquisby.benchmarks.aim.summary import create_summary_aim_data
from pquisby.benchmarks.aim.graph import graph_aim_data
from pquisby.benchmarks.autohpl.extract import extract_autohpl_data
from pquisby.benchmarks.autohpl.summary import create_summary_autohpl_data
from pquisby.benchmarks.autohpl.graph import graph_autohpl_data
from pquisby.benchmarks.speccpu.extract import extract_speccpu_data
from pquisby.benchmarks.speccpu.summary import create_summary_speccpu_data
from pquisby.benchmarks.speccpu.graph import graph_speccpu_data
from pquisby.benchmarks.speccpu.comparison import compare_speccpu_results
from pquisby.benchmarks.etcd.etcd import (
    extract_etcd_data, create_summary_etcd_data, graph_etcd_data, compare_etcd_results)
from pquisby.util import read_config,write_config

logging.basicConfig(level=logging.INFO)


def check_test_is_hammerdb(test_name):

    if test_name in ["hammerdb_pg", "hammerdb_maria", "hammerdb_mssql"]:
        return True
    else:
        return False


def process_results(results,test_name,cloud_type,OS_TYPE,OS_RELEASE,spreadsheet_name,spreadsheetId):

    """"""
    spreadsheet_name = f"{cloud_type}-{OS_TYPE}-{OS_RELEASE}-{spreadsheet_name}"

    if not spreadsheetId:
        spreadsheetId = create_spreadsheet(
            spreadsheet_name, test_name)

    # TODO: remove if check
    try:
        if check_test_is_hammerdb(test_name):
            results = create_summary_hammerdb_data(results)
        else:
            results = globals()[f"create_summary_{test_name}_data"](results,OS_RELEASE)
    except Exception as exc:
        logging.error("Error summarising "+str(test_name)+" data")
        print(str(exc))
        return
    try:
        create_sheet(spreadsheetId, test_name)
        append_to_sheet(spreadsheetId, results, test_name)
    except Exception as exc:
        logging.error("Error appending "+str(test_name)+" data to sheet")
        return
    # Graphing up data
    try:
        if check_test_is_hammerdb(test_name):
            graph_hammerdb_data(spreadsheetId, test_name)
        else:
            globals()[f"graph_{test_name}_data"](
                spreadsheetId, test_name)
    except Exception as exc:
        logging.error("Error graphing "+str(test_name)+" data")
        return

    return []


# TODO: simplify functions once data location is exact
def data_handler():
    """"""
    global test_name
    global source
    global count
    results = []
    cloud_type = read_config('cloud', 'cloud_type')
    OS_TYPE = read_config('test', 'OS_TYPE')
    OS_RELEASE = read_config('test', 'OS_RELEASE')
    spreadsheet_name = read_config('spreadsheet', 'spreadsheet_name')
    spreadsheetId = read_config('spreadsheet', 'spreadsheetId')
    test_path = read_config('test','test_path')
    results_path = read_config('test','results_location')

    # Strip empty lines from location file
    for line in fileinput.FileInput(results_path, inplace=1):
        if line.rstrip():
            print(line, end="")

    with open(results_path) as file:
        test_result_path = file.readlines()

        for data in test_result_path:
            if "test " in data:
                if results:
                    results = process_results(results,test_name,cloud_type,OS_TYPE,OS_RELEASE,spreadsheet_name,spreadsheetId)
                test_name = data.replace("test ","").replace("results_","").replace(".csv","").strip()
                source = data.split()[-1].split("_")[0].strip()
            elif "new_series" in data:
                continue
            else:
                try:
                    if test_name == "fio_run":
                        data = data.strip("\n").strip("'").strip()
                        path,system_name=(data.split(",")[0]+","+data.split(",")[1]),data.split(",")[-1]
                        path=path.replace("/"+os.path.basename(path),"")
                    else:
                        data = data.strip("\n").strip("'")
                        path, system_name = data.split(",")
                    path = test_path+"/"+path.strip()
                    if test_name == "streams":
                        ret_val = extract_streams_data(path, system_name,OS_RELEASE)
                        if ret_val:
                            results += ret_val
                    # TODO: support url fetching
                    elif test_name == "uperf":
                        ret_val = extract_uperf_data(path, system_name)
                        if ret_val:
                            results += ret_val

                    elif test_name == "linpack":
                        ret_val = extract_linpack_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    # TODO: support url fetching
                    elif test_name == "specjbb":
                        ret_value = extract_specjbb_data(path, system_name,OS_RELEASE)
                        if ret_value != None:
                            results.append(ret_value)
                    elif test_name == "pig":
                        ret_val = extract_pig_data(path, system_name,OS_RELEASE)
                        if ret_val:
                            results += ret_val
                    elif check_test_is_hammerdb(test_name):
                        ret_val = extract_hammerdb_data(
                            path, system_name, test_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "fio_run":
                        ret_val=None
                        if source == "results":
                             ret_val = extract_fio_run_data(path, system_name,OS_RELEASE)
                        elif source == "pbench":
                             ret_val = process_fio_run_result(path, system_name)
                        if ret_val:
                             results += ret_val
                        pass
                    elif test_name == "boot":
                        ret_val = extract_boot_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "aim":
                        ret_val = extract_aim_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "autohpl":
                        ret_val = extract_autohpl_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "speccpu":
                        ret_val = extract_speccpu_data(path, system_name,OS_RELEASE)
                        if ret_val:
                            results += ret_val
                    elif test_name == "etcd":
                        ret_val = extract_etcd_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    else:
                        continue

                except ValueError as exc:
                    logging.error(str(exc))
                    continue
        try:
            results = process_results(results,test_name,cloud_type,OS_TYPE,OS_RELEASE,spreadsheet_name,spreadsheetId)
        except Exception as exc:
            logging.error(str(exc))
            pass
        print(f"https://docs.google.com/spreadsheets/d/{spreadsheetId}")


def compare_results(args):

    sheet_list = []
    spreadsheet_name = []
    comparison_list = []

    spreadsheets = args.spreadsheets.split(",")
    test_name = [args.test_name] if args.test_name else []

    for spreadsheet in spreadsheets:
        sheet_names = []

        sheets = get_sheet(spreadsheet, test_name=test_name)
        spreadsheet_name.append(get_sheet(spreadsheet, test_name=[])[
                                "properties"]["title"].strip())

        for sheet in sheets.get("sheets"):
            sheet_names.append(sheet["properties"]["title"].strip())
        sheet_list.append(sheet_names)
    if test_name:
        comparison_list = test_name
    else:
        # Find sheets that are present in all spreadsheets i.e intersection
        comparison_list = set(sheet_list[0])
        for sheets in sheet_list[1:]:
            comparison_list.intersection_update(sheets)

        comparison_list = list(comparison_list)

    spreadsheet_name = " and ".join(spreadsheet_name)
    spreadsheetId = create_spreadsheet(spreadsheet_name, comparison_list[0])

    for index, test_name in enumerate(comparison_list):
        write_config("test","test_name",test_name)
        if check_test_is_hammerdb(test_name):
            compare_hammerdb_results(spreadsheets, spreadsheetId, test_name)
        else:
            globals()[f"compare_{test_name}_results"](
                spreadsheets, spreadsheetId, test_name
            )
        if index + 1 != len(comparison_list):
            logging.info(
                "# Sleeping 10 sec to workaround the Google Sheet per minute API limit"
            )
            time.sleep(10)

    print(f"https://docs.google.com/spreadsheets/d/{spreadsheetId}")


def main():
    data_handler()

if __name__ == "__main__":
    main()
