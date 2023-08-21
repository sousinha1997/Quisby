from itertools import groupby

from pquisby.lib.util import mk_int, process_instance


def fio_run_sort_data(results):
    sorted_result = []
    # group data
    results = [list(g) for k, g in groupby(results, key=lambda x: x != [""]) if k]

    # sort results together by operation and operation size
    results.sort(key=lambda x: (x[0][1], x[0][2], str(
       process_instance(x[0][0], "family", "version", "feature"))))

    for _, items in groupby(
       results, key=lambda x: (process_instance(
           x[0][0], "family", "version", "feature"), x[0][1], x[0][2])
    ):
       sorted_result += sorted(
           list(items), key=lambda x: mk_int(process_instance(x[0][0], "size"))
       )
    return sorted_result

def key_func(sublist):
    parts = sublist[0].split('_')
    d_num = int(parts[0])
    j_num = int(parts[1].split("-")[1])
    iod_num = int(parts[2].split("-")[1])
    return (d_num, j_num, iod_num, float(sublist[1]))

def create_summary_fio_run_data(results,OS_RELEASE):
    """ Create summary of the extracted raw data
        Parameters
        ----------
        results : list
            Extracted raw data from results location"""
    summary_results = []
    sort_result_disk = []
    try:
        results = fio_run_sort_data(results)
    except Exception as exc:
        print(str(exc))
    for header, items in groupby(results, key=lambda x: [x[0][0], x[0][1],  x[0][2]]):
        try:
            items = list(items)
            summary_results.append([""])
            summary_results.append([header[0], header[1], header[2]])
            summary_results.append(["iteration_name", items[0][1][1]])
            for index, item in enumerate(items):
                # Add individual data tables
                sort_result_disk.append(item[2])
            summary_results.extend(sorted(sort_result_disk, key=key_func))
            sort_result_disk = []

        except Exception as exc:
            print(str(exc))
            pass
    return summary_results
