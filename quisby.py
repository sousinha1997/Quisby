import argparse
import json
import os.path
import fileinput
import shutil
import sys
import time
from datetime import datetime

from quisby import util
from health_check import *
from quisby.benchmarks.coremark.coremark import extract_coremark_data, create_summary_coremark_data
from quisby.benchmarks.coremark.graph import graph_coremark_data
from quisby.benchmarks.coremark.compare import compare_coremark_results

from quisby.benchmarks.coremark_pro.coremark_pro import extract_coremark_pro_data, create_summary_coremark_pro_data
from quisby.benchmarks.coremark_pro.graph import graph_coremark_pro_data
from quisby.benchmarks.coremark_pro.compare import compare_coremark_pro_results

from quisby.benchmarks.passmark.passmark import extract_passmark_data, create_summary_passmark_data
from quisby.benchmarks.passmark.graph import graph_passmark_data
from quisby.benchmarks.passmark.compare import compare_passmark_results

from quisby.benchmarks.pyperf.pyperf import extract_pyperf_data, create_summary_pyperf_data
from quisby.benchmarks.pyperf.graph import graph_pyperf_data
from quisby.benchmarks.pyperf.compare import compare_pyperf_results

from quisby.benchmarks.phoronix.phoronix import extract_phoronix_data, create_summary_phoronix_data
from quisby.benchmarks.phoronix.graph import graph_phoronix_data
from quisby.benchmarks.phoronix.compare import compare_phoronix_results

from quisby.benchmarks.streams.streams import extract_streams_data, create_summary_streams_data
from quisby.benchmarks.streams.graph import graph_streams_data
from quisby.benchmarks.streams.comparison import compare_streams_results

from quisby.benchmarks.uperf.uperf import extract_uperf_data, create_summary_uperf_data
from quisby.benchmarks.uperf.graph import graph_uperf_data
from quisby.benchmarks.uperf.comparison import compare_uperf_results

from quisby.benchmarks.specjbb.specjbb import extract_specjbb_data, create_summary_specjbb_data
from quisby.benchmarks.specjbb.graph import graph_specjbb_data
from quisby.benchmarks.specjbb.comparison import compare_specjbb_results


from quisby.benchmarks.pig.extract import extract_pig_data
from quisby.benchmarks.pig.summary import create_summary_pig_data
from quisby.benchmarks.pig.graph import graph_pig_data
from quisby.benchmarks.pig.comparison import compare_pig_results


from quisby.benchmarks.linpack.extract import extract_linpack_data
from quisby.benchmarks.linpack.summary import create_summary_linpack_data
from quisby.benchmarks.linpack.graph import graph_linpack_data
from quisby.benchmarks.linpack.comparison import compare_linpack_results

from quisby.benchmarks.hammerdb.extract import extract_hammerdb_data
from quisby.benchmarks.hammerdb.summary import create_summary_hammerdb_data
from quisby.benchmarks.hammerdb.graph import graph_hammerdb_data
from quisby.benchmarks.hammerdb.comparison import compare_hammerdb_results

from quisby.benchmarks.fio.fio import process_fio_run_result, extract_fio_run_data
from quisby.benchmarks.fio.summary import create_summary_fio_run_data
from quisby.benchmarks.fio.graph import graph_fio_run_data
from quisby.benchmarks.fio.comparison import compare_fio_run_results

from quisby.benchmarks.reboot.reboot import extract_boot_data
from quisby.benchmarks.reboot.summary import create_summary_boot_data
from quisby.benchmarks.reboot.graph import graph_boot_data
from quisby.benchmarks.reboot.comparison import compare_reboot_data

from quisby.benchmarks.aim.extract import extract_aim_data
from quisby.benchmarks.aim.summary import create_summary_aim_data
from quisby.benchmarks.aim.graph import graph_aim_data
from quisby.benchmarks.aim.comparison import compare_aim_data

from quisby.benchmarks.auto_hpl.extract import extract_auto_hpl_data
from quisby.benchmarks.auto_hpl.summary import create_summary_auto_hpl_data
from quisby.benchmarks.auto_hpl.graph import graph_auto_hpl_data
from quisby.benchmarks.auto_hpl.comparison import compare_auto_hpl_results

from quisby.benchmarks.speccpu.extract import extract_speccpu_data
from quisby.benchmarks.speccpu.summary import create_summary_speccpu_data
from quisby.benchmarks.speccpu.graph import graph_speccpu_data
from quisby.benchmarks.speccpu.comparison import compare_speccpu_results

from quisby.benchmarks.etcd.etcd import extract_etcd_data, create_summary_etcd_data, graph_etcd_data, compare_etcd_results

from quisby.util import read_config, write_config
from quisby.sheet.sheet_util import clear_sheet_charts, clear_sheet_data, get_sheet, create_sheet, append_to_sheet, create_spreadsheet, permit_users
from quisby import custom_logger


def check_test_is_hammerdb(test_name):
    if test_name in ["hammerdb_pg", "hammerdb_maria", "hammerdb_mssql"]:
        return True
    else:
        return False


def process_results(results, test_name, cloud_type, os_type, os_release, spreadsheet_name, spreadsheetid):

    # Summarise data
    try:
        if results:
            if check_test_is_hammerdb(test_name):
                results = create_summary_hammerdb_data(results)
            else:
                custom_logger.info("Summarize " + test_name + " data...")
                results = globals()[f"create_summary_{test_name}_data"](results, os_release)
        else:
            custom_logger.error("No data found")
    except Exception as exc:
        custom_logger.error(str(exc))
        custom_logger.error("Failed to summarise data")
        return spreadsheetid

    # Append data
    try:
        create_sheet(spreadsheetid, test_name)
        custom_logger.info("Deleting existing charts and data from the sheet...")
        clear_sheet_charts(spreadsheetid, test_name)
        clear_sheet_data(spreadsheetid, test_name)
        custom_logger.info("Appending new " + test_name + " data to sheet...")
        append_to_sheet(spreadsheetid, results, test_name)
    except Exception as exc:
        custom_logger.error(str(exc))
        custom_logger.error("Failed to append data to sheet")
        return spreadsheetid

    # Graph up data
    try:
        custom_logger.info("Graphing " + test_name + " data...")
        if check_test_is_hammerdb(test_name):
            graph_hammerdb_data(spreadsheetid, test_name, "process")
        else:
            globals()[f"graph_{test_name}_data"](spreadsheetid, test_name, "process")
    except Exception as exc:
        custom_logger.error(str(exc))
        custom_logger.error("Failed to graph processed data")
        return spreadsheetid

    return spreadsheetid


def register_details_json(spreadsheet_name, spreadsheet_id):
    custom_logger.info("Collecting spreadsheet information...")
    home_dir = os.getenv("HOME")
    filename = home_dir + "/.quisby/config/charts.json"
    if not os.path.exists(filename):
        data = {"chartlist": {str(datetime.now()) +": "+ spreadsheet_name : spreadsheet_id}}
        with open(filename, "w") as f:
            json.dump(data, f)
    else:
        with open(filename, "r") as f:
            data = json.load(f)
        data["chartlist"][str(datetime.now())+": " + spreadsheet_name] = spreadsheet_id
        with open(filename, "w") as f:
            json.dump(data, f)
    custom_logger.info({spreadsheet_name: spreadsheet_id})


# TODO: simplify functions once data location is exact
def data_handler(proc_list):
    """"""
    global test_name
    global source
    global count
    results = []

    custom_logger.info("Loading configurations...")
    cloud_type = read_config('cloud', 'cloud_type')
    os_type = read_config('test', 'OS_TYPE')
    os_release = read_config('test', 'OS_RELEASE')
    spreadsheet_name = read_config('spreadsheet', 'spreadsheet_name')
    spreadsheetid = read_config('spreadsheet', 'spreadsheet_id')
    test_path = read_config('test', 'test_path')
    results_path = read_config('test', 'results_location')

    if not spreadsheetid:
        custom_logger.info("Creating a new spreadsheet... ")
        if not spreadsheet_name:
            spreadsheet_name = f"{cloud_type}-{os_type}-{os_release}-regression-test"
        spreadsheetid = create_spreadsheet(spreadsheet_name, "summary")
        write_config("spreadsheet", "spreadsheet_id", spreadsheetid)
        write_config("spreadsheet", "spreadsheet_name", spreadsheet_name)
        custom_logger.info("Spreadsheet name : " + spreadsheet_name)
        custom_logger.info("Spreadsheet ID : " + spreadsheetid)
    else:
        custom_logger.warning("Collecting spreadsheet information from config...")
        custom_logger.info("Spreadsheet name : " + spreadsheet_name)
        custom_logger.info("Spreadsheet ID : " + spreadsheetid)
        permit_users(spreadsheetid)
        custom_logger.info("Spreadsheet : " + f"https://docs.google.com/spreadsheets/d/{spreadsheetid}")
        custom_logger.warning("!!! Quit Application to prevent overwriting of existing data !!!")
        time.sleep(10)
        custom_logger.info("No action provided. Overwriting the existing sheet.")

    # Strip empty lines from location file
    for line in fileinput.FileInput(results_path, inplace=1):
        if line.rstrip():
            print(line, end="")


    with open(results_path) as file:
        custom_logger.info("Reading data files path provided in file : " + results_path)
        test_result_path = file.readlines()
        flag = False
        for data in test_result_path:
            if "test " in data:
                flag = False
                if results:
                    spreadsheetid = process_results(results, test_name, cloud_type, os_type, os_release,
                                                    spreadsheet_name, spreadsheetid)
                results = []
                test_name = data.replace("test ", "").strip()
                source = "results"
                if test_name in proc_list or proc_list == []:
                    flag = True
                    custom_logger.info(
                        "********************** Extracting and preprocessing " + str(test_name) + " data "
                                                                                                  "**********************")

            elif "new_series" in data:
                continue
            else:
                try:
                    if test_name == "fio_run":
                        data = data.strip("\n").strip("'").strip()
                        path, system_name = (data.split(",")[0] + "," + data.split(",")[1]), data.split(",")[-1]
                        path = path.replace("/" + os.path.basename(path), "")
                    else:
                        data = data.strip("\n").strip("'")
                        path, system_name = data.split(",")
                    path = test_path + "/" + path.strip()
                    custom_logger.debug(path)
                    if test_name == "streams" and flag == True:
                        ret_val = extract_streams_data(path, system_name, os_release)
                        if ret_val:
                            results += ret_val
                    elif test_name == "uperf" and flag == True:
                        ret_val = extract_uperf_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "linpack" and flag == True:
                        ret_val = extract_linpack_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "specjbb" and flag == True:
                        ret_value = extract_specjbb_data(path, system_name, os_release)
                        if ret_value is not None:
                            results.append(ret_value)
                    elif test_name == "pig" and flag == True:
                        ret_val = extract_pig_data(path, system_name, os_release)
                        if ret_val:
                            results += ret_val
                    elif check_test_is_hammerdb(test_name) and flag == True:
                        ret_val = extract_hammerdb_data(path, system_name, test_name, os_release)
                        if ret_val:
                            results += ret_val
                    elif test_name == "fio_run" and flag == True:
                        ret_val = None
                        if source == "results":
                            ret_val = extract_fio_run_data(path, system_name, os_release)
                        elif source == "pbench":
                            ret_val = process_fio_run_result(path, system_name)
                        if ret_val:
                            results += ret_val
                        pass
                    elif test_name == "boot" and flag == True:
                        ret_val = extract_boot_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "aim" and flag == True:
                        ret_val = extract_aim_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "auto_hpl" and flag == True:
                        ret_val = extract_auto_hpl_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "speccpu" and flag == True:
                        ret_val = extract_speccpu_data(path, system_name, os_release)
                        if ret_val:
                            results += ret_val
                    elif test_name == "etcd" and flag == True:
                        ret_val = extract_etcd_data(path, system_name)
                        if ret_val:
                            results += ret_val
                    elif test_name == "coremark" and flag == True:
                        ret_val = extract_coremark_data(path, system_name, os_release)
                        if ret_val:
                            results += ret_val
                    elif test_name == "coremark_pro" and flag == True:
                        ret_val = extract_coremark_pro_data(path, system_name, os_release)
                        if ret_val:
                            results += ret_val
                    elif test_name == "passmark" and flag == True:
                        ret_val = extract_passmark_data(path, system_name, os_release)
                        if ret_val:
                            results += ret_val
                    elif test_name == "pyperf" and flag == True:
                        ret_val = extract_pyperf_data(path, system_name, os_release)
                        if ret_val:
                            results += ret_val
                    elif test_name == "phoronix" and flag == True:
                        ret_val = extract_phoronix_data(path, system_name, os_release)
                        if ret_val:
                            results += ret_val
                    else:
                        if flag == False:
                            pass
                        else:
                            custom_logger.info("Mentioned benchmark not yet supported ! ")

                except Exception as exc:
                    custom_logger.error(str(exc))
        if results == []:
            custom_logger.info(f"https://docs.google.com/spreadsheets/d/{spreadsheetid}")
            register_details_json(spreadsheet_name, spreadsheetid)
        else:
            try:
                spreadsheetid = process_results(results, test_name, cloud_type, os_type, os_release, spreadsheet_name,
                                                spreadsheetid)
            except Exception as exc:
                custom_logger.error(str(exc))
                pass
            custom_logger.info(f"https://docs.google.com/spreadsheets/d/{spreadsheetid}")
            register_details_json(spreadsheet_name, spreadsheetid)


def compare_results(spreadsheets, comp_list):
    sheet_list = []
    spreadsheet_name = []
    comparison_list = []
    test_name = []

    custom_logger.info("Comparing the data provided..")
    custom_logger.info("Collecting list of benchmarks...")
    for spreadsheet in spreadsheets:
        sheet_names = []
        sheets = get_sheet(spreadsheet, test_name=test_name)
        spreadsheet_name.append(get_sheet(spreadsheet, test_name=[])["properties"]["title"].strip())
        for sheet in sheets.get("sheets"):
            if(sheet["properties"]["title"].strip()=="summary"):
                continue
            sheet_names.append(sheet["properties"]["title"].strip())
        sheet_list.append(sheet_names)

    if comp_list:
        comparison_list = comp_list
    else:
        # Find sheets that are present in all spreadsheets i.e intersection
        custom_logger.info("Extracting common benchmarks for comparison...")
        comparison_list = set(sheet_list[0])
        for sheets in sheet_list[1:]:
            comparison_list.intersection_update(sheets)
        comparison_list = list(comparison_list)
    custom_logger.info("Comparison list : "+str(comparison_list))
    spreadsheet_name = " and ".join(spreadsheet_name)
    spreadsheetid = read_config('spreadsheet', 'comp_id')

    if not spreadsheetid:
        custom_logger.info("Creating a new spreadsheet... ")
        spreadsheetid = create_spreadsheet(spreadsheet_name, comparison_list[0])
        write_config("spreadsheet", "comp_id", spreadsheetid)
        write_config("spreadsheet", "comp_name", spreadsheet_name)
        custom_logger.info("Spreadsheet name : " + spreadsheet_name)
        custom_logger.info("Spreadsheet ID : " + spreadsheetid)
    else:
        custom_logger.warning("Collecting spreadsheet information from config...")
        custom_logger.info("Comp spreadsheet ID : " + spreadsheetid)
        custom_logger.info("Spreadsheet : " + f"https://docs.google.com/spreadsheets/d/{spreadsheetid}")
        custom_logger.warning("!!! Quit Application to prevent overwriting of existing data !!!")
        time.sleep(10)
        custom_logger.info("No action provided. Overwriting the existing sheet.")

    for index, test_name in enumerate(comparison_list):
        try:
            custom_logger.info("**************************************** Comparing " + test_name + " value **************************************** ")
            write_config("test", "test_name", test_name)
            if check_test_is_hammerdb(test_name):
                compare_hammerdb_results(spreadsheets, spreadsheetid, test_name)
            else:
                globals()[f"compare_{test_name}_results"](spreadsheets, spreadsheetid, test_name)
            if index + 1 != len(comparison_list):
                custom_logger.info(
                    "# Sleeping 10 sec to workaround the Google Sheet per minute API limit"
                )
                time.sleep(10)
        except Exception as exc:
            custom_logger.error(str(exc))
            custom_logger.error("Benchmark " + test_name + " comparison failed")

        try:
            custom_logger.info("Graphing " + test_name + " comparison data...")
            if check_test_is_hammerdb(test_name):
                graph_hammerdb_data(spreadsheetid, test_name, "compare")
            else:
                globals()[f"graph_{test_name}_data"](spreadsheetid, test_name, "compare")
        except Exception as exc:
            custom_logger.error(str(exc))
            custom_logger.error("Failed to graph data")


    custom_logger.info(f"https://docs.google.com/spreadsheets/d/{spreadsheetid}")
    register_details_json(spreadsheet_name, spreadsheetid)


def reduce_data(proc_list):
    data_handler(proc_list)


def compare_data(s_list,comp_list):
    compare_results(s_list, comp_list)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tool to preprocess and visualise datasets")
    parser.add_argument("--config", type=str, required=False, help="Location to configuration file")
    parser.add_argument("--process",action='store_true',help="To preprocess and visualise a single dataset")
    parser.add_argument("--compare", type=str, required=False, help="To compare and plot two datasets")
    parser.add_argument("--list-benchmarks",action='store_true', help="To list supported benchmarks")
    parser.add_argument("--compare-list", type=str, required=False, help="Give specific benchmark to compare")
    parser.add_argument("--process-list", type=str, required=False, help="Give specific benchmark to process")
    parser.add_argument("--no-check", action='store_true',help="No health check")
    args = parser.parse_args()

    supported_benchmarks = ['aim', 'auto_hpl','boot', 'coremark', 'coremark_pro', 'etcd', 'fio_run', 'hammerdb_maria', 'hammerdb_mssql', 'hammerdb_pg', 'linpack', 'passmark', 'phoronix', 'pig', 'pyperf', 'specjbb', 'speccpu', 'streams', 'uperf']

    if args.list_benchmarks:
        custom_logger.info("Supported benchmarks :")
        for i in supported_benchmarks:
            print(i)
        exit(0)


    if not (args.process or args.compare):
        parser.print_help()
        exit(0)

    if not args.no_check:
        health_check()

    if not args.config:
        custom_logger.warning("No configuration path mentioned. Using default. ")
        home_dir = os.getenv("HOME")
        util.config_location = home_dir + "/.quisby/config/config.ini"
        if not os.path.exists(util.config_location):
            shutil.copy("./quisby/example.ini", util.config_location)
    else:
        util.config_location = args.config
    custom_logger.info("Config path : " + util.config_location)
    check_config_file(util.config_location)
    custom_logger.info("Health check complete...")
    print("**********************************************************************************************")
    print("**********************************************************************************************")

    if args.process:
        proc_list = []
        if args.process_list:
            proc_list = args.process_list.split(",")
        reduce_data(proc_list)
        exit(0)
    elif args.compare:
        comp_list = []
        if args.compare_list:
            comp_list = args.compare_list.split(",")
        try:
            s_list = args.compare.split(",")
            if len(s_list) > 1:
                compare_data(s_list,comp_list)
                exit(0)
            else:
                custom_logger.error("Provide two or more sheets to compare.")
                exit(0)
        except Exception as exc:
            custom_logger.error("Comparison failed. Check arguments.")
            exit(0)






