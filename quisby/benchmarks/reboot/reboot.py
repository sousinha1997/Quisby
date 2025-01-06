import re
import tarfile

def extract_boot_data(path, system_name):
    results = []

    # system_name = path.split("_")[2]
    try:
        with open(path + "/cloud_timings") as file:
            data = file.readlines()
            instance_start_time = re.findall(r"instance start_time:\s+(\d+)", data[0])[0]
            terminate_time = re.findall(r"terminate time:\s+(\d+)", data[1])[0]

    except FileNotFoundError:
        return []

    tar = tarfile.open(path + "/boot_info/initial_boot_info.tar")
    for member in tar.getmembers():
        if "initial_boot_info/boot_info" in str(member):
            file = tar.extractfile(member)
            data = file.readlines()
            decoded_lines = [line.decode('utf-8') for line in data]
            reboot_time = None
            for line in decoded_lines:
                if str(line).strip().startswith("Startup finished in"):
                    parts = line.split('=')
                    if len(parts) > 1:
                        # Strip spaces and the trailing 's' to get the numeric value
                        reboot_time = parts[1].strip().replace('s', '')
                    break  # Stop iterating once we find the line

    if instance_start_time and terminate_time and reboot_time:
        results.append(["System name", "Start Time", "Terminate Time", "Reboot Time"])
        results.append([system_name, instance_start_time, terminate_time, reboot_time])

    return results
