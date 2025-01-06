from quisby.benchmarks.linpack.graph import graph_linpack_data


def graph_auto_hpl_data(spreadsheet_id, test_name, action):
    """
    Graphs AutoHPL data based on the provided test results.

    This function calls the `graph_linpack_data` function to generate graphs
    for the AutoHPL test data based on the provided spreadsheet, test name,
    and action to be performed.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet containing the data.
        test_name (str): The name of the test for which data is to be graphed.
        action (str): The action to perform (e.g., "generate", "update", etc.) when graphing.

    Returns:
        Any: Returns the result of the `graph_linpack_data` function.
    """
    try:
        # Call the function to graph the Linpack data for AutoHPL
        return graph_linpack_data(spreadsheet_id, test_name, action)
    except Exception as e:
        # Handle potential errors and raise with a descriptive message
        raise RuntimeError(f"Error graphing AutoHPL data: {str(e)}")
