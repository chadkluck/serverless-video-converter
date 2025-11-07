import json
import os
from urllib.parse import urlparse
import uuid
import boto3

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
    
    request_id = event['Records'][0]['responseElements']['x-amz-request-id']
    user_id = event['Records'][0]['userIdentity']['principalId']
    user_ip = event['Records'][0]['requestParameters']['sourceIPAddress']
    
    print('Processing New Object: ' + source_s3)

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
        destination_s3 = f's3://{os.environ["VIDEO_OUTPUT_BUCKET"]}{os.environ["VIDEO_OUTPUT_PREFIX"]}'
                    
        print('Destination: ' + destination_s3)

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
            'application': os.environ['AWS_LAMBDA_FUNCTION_NAME'],
            'input': source_s3,
            'settings': job_name
        }
        
        region = os.environ['AWS_DEFAULT_REGION']
        endpoints = boto3.client('mediaconvert', region_name=region) \
            .describe_endpoints()
        client = boto3.client('mediaconvert', region_name=region, 
                               endpoint_url=endpoints['Endpoints'][0]['Url'], 
                               verify=True)
                               
        try:
            client.create_job(Role=os.environ['MEDIA_CONVERT_ROLE'], 
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