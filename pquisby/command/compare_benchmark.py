import click
from pquisby.lib.compare_result import compare_results


@click.command()
@click.option('-i', '--spreadsheet-id-list', help='Comma separated spreadsheet ids')
@click.option('-n', '--benchmark-name', help='Benchmark name')
def compare_benchmark(spreadsheet_id_list, benchmark_name):
    spreadsheet_name, spreadsheet_id = compare_results(spreadsheet_id_list, benchmark_name)
    print("Comparison chart -")
    print(f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")