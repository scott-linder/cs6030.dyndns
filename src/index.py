import os
import re
import boto3
import uuid

def update(event, context):
    subdomain = event['pathParameters']['subdomain']
    key = event['queryStringParameters']['key']
    ip = event['queryStringParameters']['ip']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    entry = table.get_item(
        Key={
            'id': subdomain
        }
    )
    if not 'Item' in entry or not entry['Item']['key'] == key:
        return { 'statusCode': '400', 'body': 'Invalid subdomain or key' }

    route53 = boto3.client('route53')
    route53.change_resource_record_sets(
        HostedZoneId=os.environ['ZONE_ID'],
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': subdomain + '.ibidns.com.',
                        'Type': 'A',
                        'TTL': 300,
                        'ResourceRecords': [
                            {
                                'Value': ip
                            }
                        ]
                    }
                }
            ]
        }
    )
    return { 'statusCode': '200', 'body': 'ok' }

def register(event, context):
    subdomain = event['pathParameters']['subdomain']
    # regex to match valid subdomain label
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    if not allowed.match(subdomain):
        return { 'statusCode': '400', 'body': 'invalid subdomain ' + subdomain }
    key = str(uuid.uuid4())
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    table.put_item(
        Item={
            'id': subdomain,
            'key': key
        },
        # Prevent replacing an existing entry for the given subdomain.
        ConditionExpression='attribute_not_exists(id)'
    )
    return { 'statusCode': '200', 'body': key }
