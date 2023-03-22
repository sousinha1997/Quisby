
import click
from pquisby.lib.runs import data_handler

@click.command()
@click.option('-r', '--run-name', help='Run name')
@click.option('-l', '--results-location', help="File path for results")
@click.option('-v', '--os-version', help="Distro and version")
@click.option('-c', '--controller-name', help="Controller Name")
@click.option('-i', '--spreadsheet-id', help="Any specific spreadsheet")
@click.option('-n', '--spreadsheet-name', help="Any specific spreadsheet name")
def single_run(run_name, results_location, os_version, controller_name, spreadsheet_id, spreadsheet_name):
    spreadsheet_id = data_handler(run_name, results_location, os_version, controller_name, spreadsheet_id, spreadsheet_name)
    print(f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")




        



    
                