import os
import re
import boto3
import uuid

def handler(event, context):
    subdomain = event['pathParameters']['subdomain']
    # regex to match valid subdomain label
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    if not allowed.match(subdomain):
        return { 'statusCode': '400', 'body': 'invalid subdomain ' + subdomain }
    key = uuid.uuid4()
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    table.put_item(
        Item={
            'subdomain': subdomain,
            'key': key
        },
        # Prevent replacing an existing entry for the given subdomain.
        ConditionExpression='attribute_not_exists(subdomain)'
    )
    return { 'statusCode': '200', 'body': key }