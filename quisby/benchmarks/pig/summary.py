from itertools import groupby

from quisby.util import mk_int, process_instance


def pig_sort_data_by_system_family(results):
    sorted_result = []

    results = [list(g) for k, g in groupby(results, key=lambda x: x != [""]) if k]

    results.sort(key=lambda x: str(process_instance(x[0][0], "family", "version", "feature")))

    for _, items in groupby(results, key=lambda x: process_instance(x[0][0], "family", "version", "feature")):
        sorted_result.append(
            sorted(
                list(items), key=lambda x: mk_int(process_instance(x[0][0], "size"))
            )
        )

    return sorted_result


def create_summary_pig_data(pig_data, os_release):
    results = []

    pig_data = pig_sort_data_by_system_family(pig_data)

    for items in pig_data:
        for item in items:
            results.append([""])
            results += item

    return results
