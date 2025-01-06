from quisby.benchmarks.linpack.comparison import compare_linpack_results


def compare_auto_hpl_results(spreadsheets, spreadsheet_id, test_name):
    """
    Compares AutoHPL results using Linpack benchmark data.

    This function calls the `compare_linpack_results` function to compare
    Linpack results for AutoHPL tests. It uses provided spreadsheets and test
    details to perform the comparison.

    Args:
        spreadsheets (list): A list of spreadsheet data to compare.
        spreadsheet_id (str): The ID of the spreadsheet containing the results.
        test_name (str): The name of the test to compare.

    Returns:
        None
    """
    try:
        # Call the Linpack comparison function with the provided arguments
        compare_linpack_results(spreadsheets, spreadsheet_id, test_name)
    except Exception as e:
        # Handle errors that may occur during comparison
        raise RuntimeError(f"Error comparing AutoHPL results: {str(e)}")
