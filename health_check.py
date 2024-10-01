import configparser
import os
import re
import subprocess
import sys

from quisby import custom_logger


def check_predefined_folders():
    home_dir = os.getenv("HOME")
    folders = [home_dir+'/.quisby/config/', home_dir+'/.quisby/logs/']
    for folder_path in folders:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            custom_logger.info(f"Folder '{folder_path}' created.")
        else:
            custom_logger.info(f"Folder '{folder_path}' exists...")


def is_package_installed(package_name):
    try:
        # Run pip show command to get information about the package
        result = subprocess.run(['python3.9', '-m', 'pip', 'show', package_name], capture_output=True, text=True)
        # Check if the package information contains the package name
        return package_name in result.stdout
    except Exception as e:
        print(f"Error occurred: {e}")
        return False


def check_and_install_requirements():
    """Install required packages from requirements.txt if not installed."""
    try:
        custom_logger.info("Checking if all the required packages are installed...")
        with open("requirements.txt", "r") as file:
            packages = file.read()

        # Extract package names and hashes using regular expressions
        package_info = re.findall(r"([a-zA-Z0-9_-]+)==[\d.]+(?:;\s+.*?)*(?:\s+--hash=([\w:]+))", packages)
        req = []
        # Fetch each package using pip
        for package, hashes in package_info:
            custom_logger.info(f"Checking for installation: {package}")
            if not (is_package_installed(package)):
                req.append(package)
        if req:
            custom_logger.error("Some packages not installed")
            custom_logger.info("Installing missing packages...")
            os.system("python3.9 -m pip install -r requirements.txt")
    except Exception as e:
        custom_logger.error(f"Failed to install required packages: {e}")
        sys.exit(1)


def create_virtual_environment(env_dir):
    """Create a Python virtual environment."""
    try:
        subprocess.check_call([sys.executable, '-m', 'venv', env_dir])
        custom_logger.info(f"Virtual environment created at {env_dir}")
    except subprocess.CalledProcessError:
        custom_logger.error("Failed to create virtual environment.")
        sys.exit(1)


def enter_virtual_environment(env_dir):
    """Activate the Python virtual environment."""
    activate_script = os.path.join(env_dir, 'bin', 'activate')
    if os.name == 'nt':
        activate_script = os.path.join(env_dir, 'Scripts', 'activate.bat')

    if os.path.exists(activate_script):
        try:
            subprocess.check_call([activate_script], shell=True)
            custom_logger.info("Entered virtual environment.")
        except subprocess.CalledProcessError:
            custom_logger.error("Failed to activate virtual environment.")
            sys.exit(1)
    else:
        custom_logger.error("Error: Virtual environment activation script not found.")
        sys.exit(1)


def check_virtual_environment():
    """Check if we are inside a Python 3.9 virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        custom_logger.info("Running inside a virtual environment.")
        if sys.version_info[:2] != (3, 9):
            custom_logger.info("You are not using Python 3.9 within the virtual environment.")
            sys.exit(1)
    else:
        custom_logger.warning("Not running inside a virtual environment. Create a virtual environment with python3.9. "
                              "Steps: \n 1. Create environment. < Ex: python3.9 -m venv 3.9-env >\n 2. Enter the "
                              "environment. < Ex: source 3.9-env/bin/activate >")
        # time.sleep(10)
        # create_virtual_environment()
        # enter_virtual_environment()
        sys.exit(1)


def check_python_version():
    """Check if the current Python version is 3.9."""
    if sys.version_info[:2] != (3, 9):
        custom_logger.error("Python 3.9 is required to run this script.")
        sys.exit(1)
    else:
        custom_logger.info("Python 3.9 is installed.")


def validate_config_values(config):
    test_path = config.get('test', 'test_path').strip()
    results_location = config.get('test', 'results_location').strip()
    system_name = config.get('test', 'system_name').strip()
    os_type = config.get('test', 'OS_TYPE').strip()
    os_release = config.get('test', 'OS_RELEASE').strip()
    cloud_type = config.get('cloud', 'cloud_type').strip()
    region = config.get('cloud', 'region').strip()
    flag = 0
    # Check test_name and results_location paths
    if not (test_path and os.path.exists(test_path)):
        custom_logger.error("Test path doesn't exist !")
        flag = 1
    if not (results_location and os.path.exists(results_location)):
        custom_logger.error("Results location file not present !")
        flag = 1

    if not os_type:
        custom_logger.warning("OS type not mentioned")

    if not os_release:
        custom_logger.warning("OS release not mentioned")

    # Validate cloud_type
    if cloud_type not in ['aws', 'gcp', 'azure', 'localhost']:
        custom_logger.error("Cloud type incorrect. Valid values : [aws/gcp/azure/localhost] !")
        flag = 1

    if cloud_type != "locahost":
        custom_logger.warning(
            "Check if format of regions are correctly mentioned.\nExample:\naws : us-east-1\nazure : us-east\ngcp : "
            "us-east1")

    # Warn if users is empty
    if config.has_option('access', 'users'):
        users = config.get('access', 'users').strip()
        if not users:
            custom_logger.warning("No users mentioned !")

    if flag:
        custom_logger.error("Fix the issues and try again.")
        sys.exit(1)


def check_for_config_fields(config_file):
    config = configparser.ConfigParser()
    try:
        # Check if config.ini is parasable
        config.read(config_file)

        # For example, check if required sections or options are present,
        required_fields = {
            'test': ['test_name', 'test_path', 'results_location', 'system_name', 'OS_TYPE', 'OS_RELEASE'],
            'spreadsheet': ['spreadsheet_id', 'spreadsheet_name', 'comp_id', 'comp_name'],
            'cloud': ['region', 'cloud_type'],
            'dependencies': ['specjbb_java_version'],
            'access': ['users'],
            'LOGGING': ['level', 'filename', 'max_bytes_log_file', 'backup_count']
        }

        flag = 1
        for section, fields in required_fields.items():
            for field in fields:
                if not config.has_option(section, field):
                    custom_logger.error("Missing [" + section + "] : " + field + " field in configuration file !")
                    flag = 0
        if not flag:
            sys.exit(1)

        # Checking values for the fields
        validate_config_values(config)

    except (configparser.Error, IOError):
        custom_logger.error("Invalid configuration file !")
        sys.exit(1)
    pass


def check_config_file(config_file):
    """Check if config.ini exists."""
    custom_logger.info(" !!! VALIDATING CONFIGURATION FILE !!!")
    if not os.path.isfile(config_file):
        custom_logger.error("Config.ini does not exist.")
        sys.exit(1)
    else:
        check_for_config_fields(config_file)


def health_check():
    custom_logger.info("**************************************** RUNNING QUISBY APPLICATION "
                       "**************************************** ")
    custom_logger.info(
        "User documentation at : https://docs.google.com/document/d/1g3kzp3pSMN_JVGFrFBWTXOeKaWG0jmA9x0QMAp299NI ")
    custom_logger.info("Initial Health check running...")
    check_predefined_folders()
    check_virtual_environment()
    check_python_version()
    check_and_install_requirements()

if __name__ == "__main__":
    health_check()
