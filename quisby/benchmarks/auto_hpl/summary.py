from quisby.benchmarks.linpack.summary import create_summary_linpack_data


def create_summary_auto_hpl_data(results, os_release):
    """
    Create a summary of HPL data using the create_summary_linpack_data function.

    Args:
        results (dict): The results data to summarize.
        os_release (str): The operating system release version.

    Returns:
        summary: The generated summary of the HPL data.
    """
    return create_summary_linpack_data(results, os_release)
