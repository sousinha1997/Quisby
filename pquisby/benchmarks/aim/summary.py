from itertools import groupby

from pquisby.util import mk_int


def create_summary_aim_data(results,OS_RELEASE):
    summary_results = []
    # group data
    results = [list(g) for k, g in groupby(results, key=lambda x: x != [""]) if k]

    results = sorted(
        results, key=lambda x: (x[0][1], mk_int(x[0][0].split(".")[1].split("x")[0]))
    )

    for key, items in groupby(results, key=lambda x: (x[0][1], x[0][0].split(".")[0])):
        run_data = {}

        items = list(items)
        columns = [i[0][0] + f"-{OS_RELEASE}" for i in items]
        for index, item in enumerate(items):

            for ele in item[1:]:
                if ele[0] == "Tasks":
                    continue
                if ele[0] in run_data:
                    for _ in range(index - len(run_data[ele[0]])):
                        run_data[ele[0]].append("")
                    run_data[ele[0]].append(ele[1])
                else:
                    run_data[ele[0]] = [""] * index
                    run_data[ele[0]].append(ele[1])
        summary_results.append([""])
        summary_results.append(list(key)+["Jobs/Min"])
        summary_results.append(["Load", *columns])
        for key, value in run_data.items():
            summary_results.append([key, *value])

    return summary_results
