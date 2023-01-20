import os
from os.path import isfile


def extract_aim_data(path, system_name):
    results = []

    ls_dir = os.listdir(path)

    for folder in ls_dir:
        if not isfile(path + f"/{folder}"):
            results.append([""])
            results.append([system_name, folder])
            results.append(["Tasks", "Jobs/min"])

            with open(path + f"/{folder}/xfs_aim7.txt") as txt_file:

                switch_read = False
                for line in txt_file:
                    if "Run Beginning" in line:
                        switch_read = True
                    if "Testing over" in line:
                        switch_read = False
                        break

                    if switch_read:
                        if "Tasks" in line or "AIM" in line:
                            continue
                        if line != "\n":
                            results.append(line.split()[:2])

    return results
