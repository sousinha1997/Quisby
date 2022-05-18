import os.path
import sys
import glob
import argparse
import fileinput
import time
import logging

import quisby.config as config
from quisby.sheet.sheetapi import sheet
from quisby.sheet.sheet_util import (
    get_sheet,
    create_sheet,
    append_to_sheet,
    create_spreadsheet,
)
from quisby.benchmarks.streams.streams import (
    extract_streams_data,
    create_summary_streams_data,
)
from quisby.benchmarks.streams.graph import graph_streams_data
from quisby.benchmarks.streams.comparison import compare_streams_results
from quisby.benchmarks.uperf.uperf import extract_uperf_data, create_summary_uperf_data
from quisby.benchmarks.uperf.graph import graph_uperf_data
from quisby.benchmarks.uperf.comparison import compare_uperf_results
from quisby.benchmarks.specjbb.specjbb import (
    extract_specjbb_data,
    create_summary_specjbb_data,
)
from quisby.benchmarks.specjbb.comparison import compare_specjbb_results
from quisby.benchmarks.specjbb.graph import graph_specjbb_data
from quisby.benchmarks.pig.extract import extract_pig_data
from quisby.benchmarks.pig.graph import graph_pig_data
from quisby.benchmarks.pig.summary import create_summary_pig_data
from quisby.benchmarks.pig.comparison import compare_pig_results
from quisby.benchmarks.linpack.extract import extract_linpack_data
from quisby.benchmarks.linpack.summary import create_summary_linpack_data
from quisby.benchmarks.linpack.graph import graph_linpack_data
from quisby.benchmarks.linpack.comparison import compare_linpack_results
from quisby.benchmarks.hammerdb.extract import extract_hammerdb_data
from quisby.benchmarks.hammerdb.summary import create_summary_hammerdb_data
from quisby.benchmarks.hammerdb.graph import graph_hammerdb_data
from quisby.benchmarks.hammerdb.comparison import compare_hammerdb_results
#from quisby.benchmarks.fio.fio import process_fio_result, extract_fio_data
#from quisby.benchmarks.fio.summary import create_summary_fio_run_data
#from quisby.benchmarks.fio.graph import graph_fio_run_data
from quisby.benchmarks.fio.comparison import compare_fio_results
from quisby.benchmarks.reboot.reboot import extract_boot_data
from quisby.benchmarks.reboot.summary import create_summary_boot_data
from quisby.benchmarks.reboot.graph import graph_boot_data
from quisby.benchmarks.aim.extract import extract_aim_data
from quisby.benchmarks.aim.summary import create_summary_aim_data
from quisby.benchmarks.aim.graph import graph_aim_data
from quisby.benchmarks.autohpl.extract import extract_autohpl_data
from quisby.benchmarks.autohpl.summary import create_summary_autohpl_data
from quisby.benchmarks.autohpl.graph import graph_autohpl_data
from quisby.benchmarks.speccpu.extract import extract_speccpu_data
from quisby.benchmarks.speccpu.summary import create_summary_speccpu_data
from quisby.benchmarks.speccpu.graph import graph_speccpu_data
from quisby.benchmarks.speccpu.comparison import compare_speccpu_results
from quisby.benchmarks.etcd.etcd import (
    extract_etcd_data, create_summary_etcd_data, graph_etcd_data, compare_etcd_results)


logging.basicConfig(level=logging.INFO)


def check_test_is_hammerdb(test_name):

    if test_name in ["hammerdb_pg", "hammerdb_maria", "hammerdb_mssql"]:
        return True
    else:
        return False


def process_results(results,test_name):
    """"""



    spreadsheet_name = f"{config.cloud_type}-{config.OS_TYPE}-{config.OS_RELEASE}-{config.spreadsheet_name}"
    logging.info("config.spreadsheett========"+config.spreadsheetId)

    if not config.spreadsheetId:
        config.spreadsheetId = create_spreadsheet(
            spreadsheet_name, test_name)
        logging.info("config.spreadsheett========" + config.spreadsheetId)

    logging.info("config.spreadsheett========" + config.spreadsheetId)

    # TODO: remove if check
    if check_test_is_hammerdb(test_name):
        results = create_summary_hammerdb_data(results)
    else:
        results = globals()[f"create_summary_{test_name}_data"](results)

    create_sheet(config.spreadsheetId, test_name)
    append_to_sheet(config.spreadsheetId, results, test_name)
    # Graphing up data
    if check_test_is_hammerdb(test_name):
        graph_hammerdb_data(config.spreadsheetId, test_name)
    else:
        globals()[f"graph_{test_name}_data"](
            config.spreadsheetId, test_name)
    return []


# TODO: simplify functions once data location is exact
def data_handler(args):
    """"""
    global test_name
    global source
    global count
    results = []
    config.OS_TYPE = args.os_type
    config.OS_RELEASE = args.os_release
    config.cloud_type = args.cloud_type
    path = args.location_file

    # Strip empty lines from location file
    for line in fileinput.FileInput(path, inplace=1):
        if line.rstrip():
            print(line, end="")

    with open(path) as file:
        test_result_path = file.readlines()

        for data in test_result_path:
            if "test " in data:
                if results:
                    results = process_results(results,test_name)
                test_name = data.replace("test ","").replace("results_","").replace(".csv","").strip()
                source = data.split()[-1].split("_")[0].strip()
            elif "new_series" in data:
                continue

            else:
                try:
                    if test_name == "fio_run":
                        data = data.strip("\n").strip("'").strip()
                        path,system_name=(data.split(",")[0]+","+data.split(",")[1]),data.split(",")[-1]
                        path=path.replace(os.path.basename(path),"")
                    else:
                        data = data.strip("\n").strip("'")
                        path, system_name = data.split(",")

                    path = config.test_path+"/"+path.strip()
                    if test_name == "streams":
                        ret_val = extract_streams_data(path, system_name)
                        if ret_val:
                            results += ret_val

                    # TODO: support url fetching
                    elif test_name == "uperf":
                        # ret_val = extract_uperf_data(path, system_name)
                        # if ret_val:
                        #     results += ret_val
                        pass

                    elif test_name == "linpack":

                        ret_val = extract_linpack_data(path, system_name)
                        if ret_val:
                            results += ret_val

                    # TODO: support url fetching
                    elif test_name == "specjbb":

                        results.append(extract_specjbb_data(path, system_name))

                    elif test_name == "pig":

                        ret_val = extract_pig_data(path, system_name)
                        if ret_val:
                            results += ret_val

                    elif check_test_is_hammerdb(test_name):
                        ret_val = extract_hammerdb_data(
                            path, system_name, test_name)
                        if ret_val:
                            results += ret_val

                    elif test_name == "fio_run":
                        # ret_val=None
                        # if source == "results":
                        #      ret_val = extract_fio_data(path, system_name)
                        # elif source == "pbench":
                        #      ret_val = process_fio_result(path, system_name)
                        # if ret_val:
                        #      results += ret_val
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
                        ret_val = extract_speccpu_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "etcd":
                        ret_val = extract_etcd_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    else:
                        continue

                except ValueError as exc:
                    #logging.error(str(exc))
                    continue
        try:
            results = process_results(results,test_name)
        except Exception as exc:
            #logging.error(str(exc))
            pass

        print(f"https://docs.google.com/spreadsheets/d/{config.spreadsheetId}")


def compare_results(args):

    sheet_list = []
    spreadsheet_name = []
    comparison_list = []

    spreadsheets = args.spreadsheets.split(",")
    test_name = [args.test_name] if args.test_name else []

    for spreadsheet in spreadsheets:
        sheet_names = []

        sheets = get_sheet(spreadsheet, range=test_name)
        spreadsheet_name.append(get_sheet(spreadsheet, range=[])[
                                "properties"]["title"])

        for sheet in sheets.get("sheets"):
            sheet_names.append(sheet["properties"]["title"])
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
        config.test_name = test_name
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
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        help="""
        Required commands for processing. 
        Try '<command> -h' for addtional args to be supplied
        """
    )

    location_parser = subparsers.add_parser(
        "process", help="Process location file and create spreadsheets"
    )
    location_parser.add_argument(
        "location_file",
        action="store",
        help="Specify the file containing locations of benchmark results",
    )
    location_parser.add_argument(
        "--os-type",
        action="store",
        help="Examples: 'Amazon', 'RHEL', 'Ubuntu'",
        required=True,
    )
    location_parser.add_argument(
        "--os-release",
        action="store",
        help="Examples:8.1, 18.04. Or, you can provide kernel version here",
        required=True,
    )
    location_parser.add_argument(
        "--cloud-type",
        action="store",
        help="Optional: Mention cloud type. default:AWS",
        default="AWS",
    )
    location_parser.set_defaults(func=data_handler)

    compare_parser = subparsers.add_parser(
        "compare", help="Takes two spreadsheets and creates a comparison spreadsheet"
    )
    compare_parser.add_argument(
        "--test-name",
        help="""
        Optional. If specified, it will create a single sheet comparing
        that benchmark only.
        """,
        action="store",
    )
    compare_parser.add_argument(
        "--spreadsheets",
        help="two comma seperated spreadsheets",
        action="store",
        required=True,
    )
    compare_parser.set_defaults(func=compare_results)
    args = parser.parse_args()
    try:
        func = args.func
    except AttributeError:
        parser.error("too few arguments")
    func(args)


if __name__ == "__main__":
    main()
