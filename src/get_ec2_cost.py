# get_ec2_cost.py>
import json
from pkg_resources import resource_filename


# Search product filter. This will reduce the amount of data returned by the
# get_products function of the Pricing API
FLT = '[{{"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"}},' \
      '{{"Field": "operatingSystem", "Value": "{o}", "Type": "TERM_MATCH"}},' \
      '{{"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"}},' \
      '{{"Field": "instanceType", "Value": "{t}", "Type": "TERM_MATCH"}},' \
      '{{"Field": "location", "Value": "{r}", "Type": "TERM_MATCH"}},' \
      '{{"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"}}]'


# Get current AWS price for an on-demand instance
def get_price(region, instance, os, pricing_client): 
    f = FLT.format(r=region, t=instance, o=os)
    data = pricing_client.get_products(ServiceCode='AmazonEC2', Filters=json.loads(f))
    od = json.loads(data['PriceList'][0])['terms']['OnDemand']
    id1 = list(od)[0]
    id2 = list(od[id1]['priceDimensions'])[0]
    return od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']


# Translate region code to region name. 
def get_region_name(region_code):
    default_region = 'US East (N. Virginia)'
    endpoint_file = resource_filename('botocore', 'data/endpoints.json')
    try:
        with open(endpoint_file, 'r') as f:
            data = json.load(f)
        # Botocore is using Europe while Pricing API using EU
        return data['partitions'][0]['regions'][region_code]['description'].replace('Europe', 'EU')
    except IOError:
        return default_region


# Get on demand instance cost per hour
def get_instance_price(region, instance_type, pricing_client):
    price = get_price(get_region_name(region), instance_type, 'Linux', pricing_client)
    return price
