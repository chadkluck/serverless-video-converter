import json
import os
from urllib.parse import urlparse
import uuid
import boto3

VIDEO_OUTPUT_BUCKET = [bucket.strip() for bucket in os.environ["VIDEO_OUTPUT_BUCKET"].split(',')]
VIDEO_OUTPUT_PREFIX = os.environ["VIDEO_OUTPUT_PREFIX"]
AWS_LAMBDA_FUNCTION_NAME = os.environ["AWS_LAMBDA_FUNCTION_NAME"]
AWS_REGION = os.environ["AWS_DEFAULT_REGION"]
MEDIA_CONVERT_ROLE = os.environ['MEDIA_CONVERT_ROLE']

def normalize_output_prefix(object_key, etag=None):
    """Normalize the output prefix by replacing invalid characters."""

    output_prefix = os.path.splitext(os.path.basename(object_key))[0]
    output_prefix = ''.join(c if c.isalnum() or c in '-_' else '_' for c in output_prefix)
    output_prefix = '_'.join(filter(None, output_prefix.split('_')))
    output_prefix = output_prefix.strip('_')
    output_prefix = output_prefix.strip('-')
    if etag is None:
        etag = str(uuid.uuid4())
        etag = etag.replace('-', '')

    output_prefix = output_prefix + '-' + etag[:8]

    return output_prefix

"""
When you run an S3 Batch Operations job, your job  
invokes this Lambda function. Specifically, the Lambda function is 
invoked on each video object listed in the manifest that you specify 
for the S3 Batch Operations job in Step 5.  

Input parameter "event": The S3 Batch Operations event as a request
for the Lambda function.

Input parameter "context": Context about the event.

Output: A result structure that Amazon S3 uses to interpret the result 
        of the operation. It is a job response returned back to S3 Batch Operations.
"""
def handler(event, context):
    
    print(event)

    source_s3_key = event['Records'][0]['s3']['object']['key']
    source_s3_bucket = event['Records'][0]['s3']['bucket']['name']
    source_s3 = 's3://' + source_s3_bucket + '/' + source_s3_key
    source_etag = event['Records'][0]['s3']['object']['eTag']
    
    request_id = event['Records'][0]['responseElements']['x-amz-request-id']
    user_id = event['Records'][0]['userIdentity']['principalId']
    user_ip = event['Records'][0]['requestParameters']['sourceIPAddress']
    
    print('Processing New Object: ' + source_s3)

    # Get S3 tags to determine output bucket
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    try:
        tags_response = s3_client.get_object_tagging(Bucket=source_s3_bucket, Key=source_s3_key)
        tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}
        
        if 'VideoOutputBucket' in tags:
            tagged_bucket = tags['VideoOutputBucket']
            if tagged_bucket in VIDEO_OUTPUT_BUCKET:
                output_bucket = tagged_bucket
            else:
                raise ValueError(f"Tagged VideoOutputBucket '{tagged_bucket}' not in allowed buckets: {VIDEO_OUTPUT_BUCKET} - Please check for typos or add the bucket to the VideoOutputBucket parameter")
        else:
            output_bucket = VIDEO_OUTPUT_BUCKET[0]
    except Exception as e:
        if 'NoSuchTagSet' in str(e):
            output_bucket = VIDEO_OUTPUT_BUCKET[0]
        else:
            raise

    output_prefix = normalize_output_prefix(source_s3_key, source_etag)
    destination_s3 = f's3://{output_bucket}{VIDEO_OUTPUT_PREFIX}{output_prefix}'

    print('Destination: ' + destination_s3)

    result_list = []
    result_code = 'Succeeded'
    result_string = 'The input video object was submitted successfully.'

    # The type of output group determines which media players can play 
    # the files transcoded by MediaConvert.
    # For more information, see Creating outputs with AWS Elemental MediaConvert.
    output_group_type_dict = {
        'HLS_GROUP_SETTINGS': 'HlsGroupSettings',
        'FILE_GROUP_SETTINGS': 'FileGroupSettings',
        'CMAF_GROUP_SETTINGS': 'CmafGroupSettings',
        'DASH_ISO_GROUP_SETTINGS': 'DashIsoGroupSettings',
        'MS_SMOOTH_GROUP_SETTINGS': 'MsSmoothGroupSettings'
    }

    try:
        job_name = 'Default'
        with open('job.json') as file:
            job_settings = json.load(file)

        job_settings['Inputs'][0]['FileInput'] = source_s3

        # The path of each output video is constructed based on the values of 
        # the attributes in each object of OutputGroups in the job.json file. 

        for output_group in job_settings['OutputGroups']:
            output_group_type = output_group['OutputGroupSettings']['Type']
            if output_group_type in output_group_type_dict.keys():
                output_group_type = output_group_type_dict[output_group_type]
                output_group['OutputGroupSettings'][output_group_type]['Destination'] = \
                    "{0}{1}".format(destination_s3,
                                    urlparse(output_group['OutputGroupSettings'][output_group_type]['Destination']).path)
            else:
                raise ValueError("Exception: Unknown Output Group Type {}."
                                 .format(output_group_type))

        job_metadata_dict = {
            'assetID': str(uuid.uuid4()),
            'application': AWS_LAMBDA_FUNCTION_NAME,
            'input': source_s3,
            'settings': job_name
        }
        
        endpoints = boto3.client('mediaconvert', region_name=AWS_REGION) \
            .describe_endpoints()
        client = boto3.client('mediaconvert', region_name=AWS_REGION, 
                               endpoint_url=endpoints['Endpoints'][0]['Url'], 
                               verify=True)
                               
        try:
            client.create_job(Role=MEDIA_CONVERT_ROLE, 
                              UserMetadata=job_metadata_dict, 
                              Settings=job_settings)
        # You can customize error handling based on different error codes that 
        # MediaConvert can return.
        # For more information, see MediaConvert error codes. 
        # When the result_code is TemporaryFailure, S3 Batch Operations retries 
        # the task before the job is completed. If this is the final retry, 
        # the error message is included in the final report.
        except Exception as error:
            result_code = 'TemporaryFailure'
            raise
    
    except Exception as error:
        if result_code != 'TemporaryFailure':
            result_code = 'PermanentFailure'
        result_string = str(error)

    finally:
        result_list.append({
            'resultCode': result_code,
            'resultString': result_string
        })
        
    response_dict = {
        'request_id': request_id,
        'source': source_s3,
        'user_id': user_id,
        'user_ip': user_ip,
        'results': result_list
    }
    
    print(response_dict)
    
    return response_dict