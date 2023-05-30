import re
from configparser import ConfigParser

invalid_compare_list = ["pig"]


def process_instance(instance_name, *args):
    pattern = r"(?P<family>\D+)(?P<size>\d+)"
    regex_match = re.match(pattern, instance_name, flags=re.IGNORECASE)
    if "size" in args:
        return regex_match.group(2)
    else:
        return regex_match.group(1)


def stream_to_csv(data):
    split_rows = data.split("\n")
    csv_data = []
    for row in split_rows:
        csv_data.append(row.split(","))
    return csv_data


def mk_int(string):
    if string:
        string = string.strip()
        return int(string) if string else 1
    else:
        return 1


def create_parser():
    configur = ConfigParser()
    return configur

def read_config(config_path,section,key):
    configur=create_parser()
    with open(config_path) as configfile:
        configur.read(config_path)
        if configur.get(section,key) is not None:
            return configur.get(section,key)
        else:
            return None

def write_config(config_path, section,key,value):
    configur=create_parser()
    configur.read(config_path)
    configur.set(section, key, value)
    with open(config_path,"w") as configfile:
        configur.write(configfile)

def merge_lists_alternately(results, list1, list2):
    merger_list = []

    merger_list.append(list1[0])
    for item1, item2 in zip(list1[1:], list2[1:]):
        merger_list.append(item1)
        merger_list.append(item2)

    results.append(merger_list)

    # row = [None] * (len(item1[1:]) + len(item2[1:]))
    # row[::2] = item1[1:]
    # row[1::2] = item2[1:]
    # results.append([item2[0]] + row)

    return results


def combine_two_array_alternating(results, value, ele, test_name):
    indexer = []

    for lindex, item1 in enumerate(value[0][1:]):
        for rindex, item2 in enumerate(ele[0][1:]):
            if item1.split("-", 1)[0] == item2.split("-", 1)[0]:
                indexer.append([lindex, rindex])
            elif test_name in invalid_compare_list:
                indexer.append([lindex, rindex])

    for list1, list2 in zip(value, ele):
        holder_list = []
        holder_list.append(list1[0])

        for index in indexer:
            holder_list.append(list1[index[0] + 1])
            holder_list.append(list2[index[1] + 1])

        results.append(holder_list)

    return results
