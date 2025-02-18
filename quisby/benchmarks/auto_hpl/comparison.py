from quisby.benchmarks.linpack.comparison import compare_linpack_results


def compare_auto_hpl_results(spreadsheets, spreadsheet_id, test_name):
    """
    Compare HPL results using the compare_linpack_results function.

    Args:
        spreadsheets (list): The list of spreadsheets to compare.
        spreadsheet_id (str): The ID of the spreadsheet.
        test_name (str): The name of the test to compare results for.
    """
    compare_linpack_results(spreadsheets, spreadsheet_id, test_name)
