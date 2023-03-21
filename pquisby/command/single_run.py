from email.policy import default
import click
from pquisby.lib.benchmarks.uperf.uperf import extract_uperf_data
from pquisby.lib.process_result import process_results

@click.command()
@click.option('--run-name', help='Run name')
@click.option('--results-location', help="File path for results")
@click.option('--os-version', help="Distro and version")
@click.option('--controller-name', help="Controller Name")
def single_run(run_name, results_location, os_version, controller_name):
    with open(results_location,"r") as results_file_data:
        results_file_data.readlines()
    test_name = None
    for data in results_file_data:
        if data.startswith("test "):
            if results:
                spreadsheetId = process_results(results,test_name,os_version, spreadsheet_name,spreadsheetId)
                results=[]
                test_name = data.replace("test ","").replace("results_","").replace(".csv","").strip()
        
        



    
                