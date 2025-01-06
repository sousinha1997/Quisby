# Using this package which is a HTTP library
from quisby import custom_logger
import sys
import json
import requests
import boto3
from quisby.util import process_instance, read_config
import os

homedir = os.getenv("HOME")
json_path = homedir + "/.quisby/config/azure_prices.json"


def fetch_from_url():
    url = "https://azure.microsoft.com/api/v3/pricing/virtual-machines/calculator"
    try:
        response = requests.get(url)
    except Exception as exc:
        custom_logger.error(str(exc))
    if response.status_code == 200:
        return response.json()
    else:
        custom_logger.error("Error: {}".format(response.text))
        return None


def get_azure_pricing(instance_name, region):
    prefix = instance_name.split("_")
    series = ""
    version = ""
    tier = ""
    try:
        series = prefix[1].lower()
        tier = prefix[0].lower()
        version = prefix[2].lower()
    except Exception as exc:
        custom_logger.debug(str(exc))
        custom_logger.info("Version not present")
    vm = "linux-" + series + version + "-" + tier

    if os.path.exists(json_path):
        # fetch price information from json
        try:
            with open(json_path) as f:
                data = json.load(f)
        except Exception as exc:
            custom_logger.error("Error extracting data from file. File corrupted. Redirecting to url fetching.")
            data = fetch_from_url()
    else:
        # fetch price information from url
        data = fetch_from_url()
        with open(json_path, 'w') as file:
            # Step 3: Dump the JSON data into the file
            json.dump(data, file, indent=4)
    if data is None:
        return data
    price = data["offers"][vm]['prices']['perhour'][region]["value"]
    return price


def get_gcp_prices(instance_name, region):
    url = "https://cloudpricingcalculator.appspot.com/static/data/pricelist.json"

    response = requests.get(url, stream=True)
    decoded_response = response.content.decode("UTF-8")
    google_ext_prices = json.loads(decoded_response)
    price_data = {}
    if "gcp_price_list" not in google_ext_prices:
        sys.stderr.write('Google Cloud pricing data missing "gcp_price_list" node\n')
        return None
    prefix = ""
    gcp_price_list = google_ext_prices["gcp_price_list"]
    family, model, cpu = instance_name.split("-")
    if family.upper() in ("N2", "N2D", "T2D", "T2A", "C2", "C2D", "M1", "M2", "N1", "E2", "C4A", "C3D"):
        prefix = "CP-COMPUTEENGINE-" + family.upper() + "-PREDEFINED-VM-CORE".strip()
    else:
        custom_logger.error("Machine price is not available for :" + instance_name)
        return None

    for name, prices in gcp_price_list.items():
        if prefix == name:
            for key, price in prices.items():
                if region == key:
                    return gcp_price_list[name][region] * float(cpu)
            custom_logger.error("Machine price is not available for region:" + region)
            return None


def get_aws_pricing(instance_type, region, os_type):
    try:
        max_price = 0.0
        filters = [
                {'Type': 'TERM_MATCH', 'Field': 'servicecode', 'Value': 'AmazonEC2'},
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                {'Type': 'TERM_MATCH', 'Field': 'regionCode', 'Value': region},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
                {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
            ]

        ec2_client = boto3.client('pricing', region_name='us-east-1')
        pricing_data_list = ec2_client.get_products(ServiceCode='AmazonEC2',
                                                    Filters=filters)['PriceList']
        for pricing_data in pricing_data_list:
            pricing_data = json.loads(pricing_data)
            product_dict = pricing_data.get('product')
            product_sku = product_dict['sku']
            on_demand_terms = pricing_data.get('terms', {}).get('OnDemand', {})
            for product_key, product_values in on_demand_terms.items():
                if product_sku in product_key:
                    ondemand_sku = product_values.get('sku')
                    for price_key, price_values in product_values.get('priceDimensions', {}).items():

                        if ondemand_sku in price_key:
                            max_price = max(max_price, float(price_values.get('pricePerUnit', {}).get('USD', 0)))
    except Exception as exc:
        print("Unable to fetch prices of " + instance_type + " for os_type " + os_type + " in region " + region)
        return None
    return max_price


def list_aws_regions(region):
    try:
        ec2 = boto3.client('ec2',region)
        regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']
                   if region['OptInStatus'] != 'not-opted-in']
        return regions
    except Exception as exc:
        print("Unable to fetch aws regions")
        return None


def list_operating_systems(region):
    try:
        client = boto3.client('pricing', region_name=region)

        response = client.get_products(ServiceCode='AmazonEC2')

        operating_systems = set()

        if 'PriceList' in response:
            for price_list in response['PriceList']:
                product = json.loads(price_list)
                if 'attributes' in product['product']:
                    attributes = product['product']['attributes']
                    if 'operatingSystem' in attributes:
                        os = attributes['operatingSystem']
                        operating_systems.add(os)
        return operating_systems
    except Exception as exc:
        print("Unable to fetch OS list")
        return None


def get_aws_instance_info(instance_name, region):
    """
    AWS pricing is retreived using the aws boto3 client pricing API.

    Following args are used for filtering results
    :instance_name: eg: "m5.2xlarge"
    :region: eg: "US East (N. Virginia)"

    returns: integer pricing in USD
    """
    pricing = boto3.client("pricing", region_name=region)

    OPERATING_SYSTEM = "AmazonEC2"
    response = pricing.get_products(
        ServiceCode=OPERATING_SYSTEM,
        Filters=[
            {
                'Type': 'TERM_MATCH',
                'Field': 'ServiceCode',
                'Value': OPERATING_SYSTEM,

            },
        ],
        FormatVersion='aws_v1',
        MaxResults=1
    )

    return response['PriceList']


def get_instance_vcpu_count(instance_type, region):
    ec2 = boto3.client('ec2', region_name=region)

    instance_info = ec2.describe_instance_types(InstanceTypes=[instance_type])

    if 'InstanceTypes' in instance_info:
        instance = instance_info['InstanceTypes'][0]
        vcpu_count = instance['VCpuInfo']['DefaultVCpus']
        return vcpu_count
    else:
        return None


def get_cloud_pricing(instance_name, region, cloud_type,os_type):
    if cloud_type == "aws":
        return get_aws_pricing(instance_name, region,os_type)

    elif cloud_type == "azure":
        return get_azure_pricing(instance_name, region)

    elif cloud_type == "gcp":
        return get_gcp_prices(instance_name, region)

    elif cloud_type == "local":
        return 1


def get_cloud_cpu_count(instance_name, region, cloud_type):
    if cloud_type == "aws":
        return get_instance_vcpu_count(instance_name, region)

    elif cloud_type == "azure":
        return int(process_instance(instance_name, "size"))

    elif cloud_type == "gcp":
        return int(process_instance(instance_name, "size"))

    elif cloud_type == "local":
        return 1


if __name__ == "__main__":
    print(get_azure_pricing("Standard_D32s_v3","us-east"))
    # print(get_gcp_prices("n2-standard-16",region)
    region = "us-east-1"
    # Replace with your desired AWS region
    instance_type = ["m6i.xlarge", "m6i.24xlarge"]  # Replace with your desired EC2 instance type
    os_type = ["rhel", "Linux", "Ubuntu Pro"]
    list_aws_regions(region)
    list_operating_systems(region)
    for instance in instance_type:
        for os in os_type:
            get_instance_vcpu_count(instance, region)
            get_aws_pricing(instance,region, os)
