from itertools import groupby

from quisby.util import mk_int, process_instance


def create_summary_speccpu_data(results, OS_RELEASE):
    sorted_result = []
    results = [list(g) for k, g in groupby(results, key=lambda x: x != [""]) if k]
    results.sort(
        key=lambda x: str(process_instance(x[0][0], "family", "version", "feature"))
    )

    for _, items in groupby(
            results, key=lambda x: process_instance(x[0][0], "family", "version", "feature")
    ):
        sorted_result.append(
            sorted(list(items), key=lambda x: mk_int(process_instance(x[0][0], "size")))
        )

    results = []

    for items in sorted_result:
        for item in items:
            results.append([""])
            results += item

    return results
