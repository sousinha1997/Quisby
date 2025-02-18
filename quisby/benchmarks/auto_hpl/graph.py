from quisby.benchmarks.linpack.graph import graph_linpack_data


def graph_auto_hpl_data(spreadsheet_id, test_name, action):
    """
    Graph the HPL data using the graph_linpack_data function.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet.
        test_name (str): The name of the test.
        action (str): The action to be performed on the data.

    Returns:
        result: The result of the graphing action.
    """
    return graph_linpack_data(spreadsheet_id, test_name, action)
