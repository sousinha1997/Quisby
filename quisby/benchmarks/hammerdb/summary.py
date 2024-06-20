from itertools import groupby

from quisby.util import mk_int, process_instance


def hammerdb_sort_data_by_system_family(results):
    sorted_result = []

    results = [list(g) for k, g in groupby(results, key=lambda x: x != [""]) if k]

    results.sort(key=lambda x: str(process_instance(x[0][1], "family", "version", "feature")))

    for _, items in groupby(results, key=lambda x: process_instance(x[0][1], "family", "version", "feature")):
        sorted_result.append(
            sorted(list(items), key=lambda x: mk_int(process_instance(x[0][1], "size")))
        )

    return sorted_result


def create_summary_hammerdb_data(hammerdb_data):
    results = []

    hammerdb_data = hammerdb_sort_data_by_system_family(hammerdb_data)

    for data in hammerdb_data:
        run_data = {}

        results.append([""])
        results.append([data[0][0][0]])

        for row in data:

            results[-1] += [row[0][1]]

            for ele in row[1:]:
                if ele[0] in run_data:
                    run_data[ele[0]].append(ele[1])
                else:
                    run_data[ele[0]] = [ele[1]]

        for key, item in run_data.items():
            results.append([key, *item])

    return results
