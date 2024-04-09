#!/usr/bin/env python3
import requests
import json
from tabulate import tabulate


def build_pricing_table(json_data, table_data):
    for item in json_data['Items']:
        meter = item['meterName']
        table_data.append([item['armSkuName'], item['retailPrice'], item['unitOfMeasure'], item['armRegionName'], meter,
                           item['productName']])


def main():
    table_data = []
    table_data.append(['SKU', 'Retail Price', 'Unit of Measure', 'Region', 'Meter', 'Product Name'])

    api_url = "https://prices.azure.com/api/retail/prices?api-version=2021-10-01-preview"
    query = "armRegionName eq 'eastus' and armSkuName eq 'Standard_D32s_v3' and meterName eq 'D32s v3' and serviceName eq 'Virtual Machines' and priceType eq 'Consumption' and productName eq 'Virtual Machines DSv3 Series'"
    # query = "armRegionName eq 'eastus' and armSkuName eq 'Standard_D32s_v3'"
    response = requests.get(api_url, params={'$filter': query})
    print(response.text)
    json_data = json.loads(response.text)

    build_pricing_table(json_data, table_data)
    nextPage = json_data['NextPageLink']

    while (nextPage):
        response = requests.get(nextPage)
        json_data = json.loads(response.text)
        nextPage = json_data['NextPageLink']
        build_pricing_table(json_data, table_data)

    print(tabulate(table_data, headers='firstrow', tablefmt='psql'))


if __name__ == "__main__":
    main()