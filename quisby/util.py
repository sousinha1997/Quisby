import re
from configparser import ConfigParser
import os

home_dir = os.getenv("HOME")
config_location = None

invalid_compare_list = ["pig"]


def create_parser():
    configur = ConfigParser()
    return configur


def read_config(section, key):
    global config_location
    configur = create_parser()
    with open(config_location) as configfile:
        configur.read(config_location)
        if configur.get(section,key) is not None:
            return configur.get(section,key)
        else:
            return None


def read_value(section, key):
    global config_location
    configur = create_parser()
    with open("threshold.ini") as configfile:
        configur.read("threshold.ini")
        if configur.get(section, key) is not None:
            return configur.get(section, key)
        else:
            return None


def write_config(section,key,value):
    configur = create_parser()
    global config_location
    configur.read(config_location)
    configur.set(section, key, value)
    with open(config_location,"w") as configfile:
        configur.write(configfile)


def process_instance(instance_name, *args):
    cloud_type = read_config("cloud","cloud_type")
    """Process the instance name to extract cloud details based on regex patterns."""
    if "local" in instance_name:
        cloud_type = "local"
        machine = "local"
    else:
        machine = instance_name

    # Define regex patterns based on cloud type
    patterns = {
        "azure": r"Standard_(?P<family>\w)(?P<size>\d+)(?P<feature>\w*)_(?P<version>\w\d)",
        "aws": r"(?P<family>\w)(?P<version>\d)(?P<feature>\w+)?.(?P<size>\d+)?(?P<bool_xlarge>x)?(?P<machine_type>\w+)",
        "gcp": r"(?P<family>\w)(?P<version>\d)(?P<sub_family>\w)?-(?P<feature>\w+)?-(?P<size>\d+)?",
        "local": r"(?P<family>\D+)"
    }

    # Select the pattern based on the cloud type
    pattern = patterns.get(cloud_type, r"")

    # Apply the regex
    regex_match = re.match(pattern, machine, flags=re.IGNORECASE)
    if not regex_match:
        return None
    return regex_match.group(*args)


def process_group(label_name, *args):
    cloud_type = read_config("cloud","cloud_type")
    if cloud_type == "azure":
        pattern = r"Standard_(?P<family>\w)(?P<sub_family>\D)?(?P<size>\d+)(?P<feature>\w+)?_(?P<accel_type>\w\d)?_?(?P<version>\w\d)"

    if cloud_type == "aws":
        pattern = r"(?P<family>\w)(?P<version>\d)(?P<feature>\w+)?.(?P<size>\d+)?(?P<bool_xlarge>x)?(?P<machine_type>\w+)"

    if cloud_type == "gcp":
        pattern = r"(?P<family>\w)(?P<version>\d)(?P<sub_family>\w)?-(?P<feature>\w+)?-(?P<size>\d+)?"

    if cloud_type == "local":
        pattern = r"(?P<family>\D+)(?P<size>\d+)"
        regex_match = re.match(pattern, label_name, flags=re.IGNORECASE)
        if "size" in args:
            return regex_match.group(2)
        else:
            return regex_match.group(1)

    regex_match = re.match(pattern, label_name, flags=re.IGNORECASE)
    return regex_match.group(*args)

def mk_int(string):
    """Convert string to an integer, return 1 for 'local' or empty strings."""
    if string == 'local':
        return 1
    if string:
        string = string.strip()
        return int(string) if string else 1
    return 1

def percentage_deviation(item1,item2):
    item1 = float(item1)
    item2 = float(item2)

    if (item1 == 0.0 == item2):
        percentage_deviation = None
    elif (item1 == 0.0):
        percentage_deviation = None
    elif (item2 == 0.0):
        percentage_deviation = None
    else:
        percentage_deviation = ((item2 - item1) / item1) * 100
    return round(percentage_deviation, 6)


def merge_lists_alternately(results, list1, list2):
    if list1[0] != list2[0]:
        return results
    merger_list = [list1[0]]
    for item1, item2 in zip(list1[1:], list2[1:]):
        merger_list.append(item1)
        merger_list.append(item2)
        try:
            dev = percentage_deviation(item1, item2)
            if dev >= 0:
                merger_list.append(dev)
            else:
                merger_list.append(dev)
        except Exception as exc:
            if item1 == "fail" or item2 == "fail" or str(item1) == str(0) or str(item2) == str(0):
                merger_list.append("Failed")
            else:
                merger_list.append("%Diff")
    results.append(merger_list)

    # row = [None] * (len(item1[1:]) + len(item2[1:]))
    # row[::2] = item1[1:]
    # row[1::2] = item2[1:]
    # results.append([item2[0]] + row)

    return results


def combine_two_array_alternating(results, value, ele):
    indexer = []
    test_name = read_config("test", "test_name")

    for lindex, item1 in enumerate(value[0][1:]):
        for rindex, item2 in enumerate(ele[0][1:]):
            if item1.split("-", 1)[0] == item2.split("-", 1)[0]:
                indexer.append([lindex, rindex])
            elif test_name in invalid_compare_list:
                indexer.append([lindex, rindex])

    for list1, list2 in zip(value, ele):
        holder_list = [list1[0]]

        for index in indexer:
            item1 = list1[index[0] + 1]
            item2 = list2[index[1] + 1]
            holder_list.append(item1)
            holder_list.append(item2)
            try:
                dev = percentage_deviation(item1, item2)
                if dev >= 0:
                    holder_list.append(dev)
                else:
                    holder_list.append(dev)
            except Exception as exc:
                if item1 == "fail" or item2 == "fail" or str(item1) == str(0) or str(item2) == str(0):
                    holder_list.append("Failed")
                else:
                    holder_list.append("%Diff")
        results.append(holder_list)
    return results

