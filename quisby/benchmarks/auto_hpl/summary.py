from quisby.benchmarks.linpack.summary import create_summary_linpack_data


def create_summary_auto_hpl_data(results, os_release):
    """
    Creates a summary of AutoHPL test results.

    This function calls `create_summary_linpack_data` to generate a summary of
    the AutoHPL test results based on the provided data and OS release information.

    Args:
        results (list): The test results to be summarized.
        os_release (str): The operating system release version used for the test.

    Returns:
        Any: Returns the summary data generated by `create_summary_linpack_data`.
    """
    try:
        # Call the function to create the summary for AutoHPL test results
        return create_summary_linpack_data(results, os_release)
    except Exception as e:
        # Handle potential errors and raise with a descriptive message
        raise RuntimeError(f"Error creating summary for AutoHPL data: {str(e)}")
