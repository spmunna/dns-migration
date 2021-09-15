import boto3
#import json
import sys
import configparser
import json

parser = configparser.ConfigParser()
parser.read("migration.config")

hostedZoneId=sys.argv[1]

client = boto3.client('route53')

paginator = client.get_paginator('list_resource_record_sets')

try:
    source_zone_records = paginator.paginate(HostedZoneId=hostedZoneId)
    for record_set in source_zone_records:
        for record in record_set['ResourceRecordSets']:
            if record['Type'] == 'NS':
                print(record['Name'])
                response = client.change_resource_record_sets(
                    HostedZoneId=hostedZoneId,
                    ChangeBatch={
                        'Comment': 'Update TTL',
                        'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': record['Name'],
                                'Type': 'NS',
                                'TTL': int(parser.get("config", "ns_ttl")),
                                'ResourceRecords': record['ResourceRecords']
                            }
                        },
                        ]
                    }
                )
                print(response)
            if record['Type'] == 'SOA':
                print(record['Name'])
                response = client.change_resource_record_sets(
                    HostedZoneId=hostedZoneId,
                    ChangeBatch={
                        'Comment': 'Update TTL',
                        'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': record['Name'],
                                'Type': 'SOA',
                                'TTL': int(parser.get("config", "soa_ttl")),
                                'ResourceRecords': record['ResourceRecords']
                            }
                        },
                        ]   
                    }
            )

except Exception as error:
    print('An error occurred getting source zone records:')
    print(str(error))
    raise
