# Serverless Video Conversion using AWS Elemental MediaConvert

> This is still in beta

AWS Lambda (Python) function triggered when a new video is uploaded to S3. The Lambda function then submits a job to AWS Elemental MediaConvert

This application is useful for scenarios such as:
- User-generated content platforms where users upload videos that need to be transcoded for streaming
- Automated video processing pipelines for media companies
- Any serverless architecture requiring video transcoding capabilities without managing servers

> For use with template-pipeline.yml which can be deployed using [Atlantis Configuration Repository for Serverless Deployments using AWS SAM](https://github.com/63Klabs/atlantis-cfn-configuration-repo-for-serverless-deployments). The application template was adapted from [Starter 01 - Basic API Gateway and Lambda using Python](https://github.com/63Klabs/atlantis-starter-00-basic-apigw-lambda-nodejs)

> NOTE! While this is serverless, meaning you only get charged for what you use, not for any idle time, you ARE charged for what you use. My personal experience in converting a 30 min video and 10 3 min videos (approx 60 min total) from 4K to 4K Optimized, 1080, 720, and SD and Stream chunks in `us-east-2` has cost about USD$100.

So, while free to set up, and you don't get charged for having it sit there, there is a cost if you USE it. If you are just experimenting I suggest having a 30 to 60 second video ready for testing and only upload large videos when you are in production and serious about hosting video content.

## Demo

This application stack is used in conjunction with S3 fronted by CloudFront and a React-based site hosted on AWS Amplify on my personal hobby site [Doghouse Lights](https://doghouselights.com/videos) under the Videos section. This application processes the videos I upload to then be streamed in various formats and sizes depending on device or network connection.

## Work Flow

1. User (or a process) uploads a video file to S3 bucket (`VideoSourceBucket`)
2. S3 triggers Lambda function (`SubmitJobFunction`)
3. Lambda function submits a job to AWS Elemental MediaConvert to transcode the video into
   multiple formats and resolutions. The job contains information on where to put the output and the IAM Role to use.
4. Transcoded videos are saved to another S3 bucket (`VideoOutputBucket`)

```mermaid
flowchart TD
    A[User uploads video file] -.->|"1. Upload"| B[S3: VideoSourceBucket]
    B -->|"2. Trigger"| C[Lambda: SubmitJobFunction]
    C -.->|"3. Submit job"| D[AWS Elemental MediaConvert]
    D -.->|"4. Save transcoded videos"| E[VideoOutputBucket]
```

To maintain a micro-service, this stack ONLY manages processing of the video. It can be part of an event-driven process pipeline.

You will still need a mechanism to upload to the `VideoSourceBucket` (CLI or web based site) and an `VideoOutputBucket` that can be fronted by CloudFront. (Additional templates are provided by 63Klabs to maintain the S3 fronted by CloudFront stacks)

## Usage

This uses the [63Klabs Atlantis developer platform](https://github.com/63Klabs/atlantis-cfn-configuration-repo-for-serverless-deployments) to manage the pipeline and storage stacks.

This is one part of a multi-stack deployment. Think of it as part of a chain of events. It could even be extended into a step function that not only sends jobs to [MediaConvert](https://aws.amazon.com/mediaconvert/), but also [Amazon Rekognition](https://aws.amazon.com/rekognition/) and [Amazon Transcribe](https://aws.amazon.com/transcribe/).

### Uploads

The video object can be placed in the `VideoSourceBucket` from the cli:

```bash
aws s3 cp large-video-file.mp4 s3://VIDEO_SOURCE_BUCKET/uploads/
```

Or using a separate process such as an online video upload mechanism or other automated process.

### Output

You will need an output bucket (and S3 object prefix) that you will pass to the stack as `VideoOutputBucket` and `VideoOutputPrefix` parameters respectively. This can either be a bucket for public consumption via CloudFront, or a drop bucket that is then picked up by the next process.

The output bucket must be configured to allow AWS Elemental MediaConvert to write to it. See [AWS Documentation](https://docs.aws.amazon.com/mediaconvert/latest/ug/setting-up-s3-buckets.html) for details.

## Deployment

This stack is designed to be deployed using the [63Klabs Atlantis developer platform](https://github.com/63Klabs/atlantis-cfn-configuration-repo-for-serverless-deployments). 

Like any other project, you can skip the Atlantis platform and go at it on your own by modifying the code and templates to fit your needs. However, if you are managing many projects manually (especially on your own or part of a small team), the Atlantis platform is highly recommended as it implements Platform Engineering and AWS best practices. Plus it utilizes AWS native resources including SAM deployments and CloudFormation without the need of proprietary DevOps tools. Everything is API, CloudFormation template, and SAM CLI based. There are a lot of logging, metrics, and security features already baked into the templates so you don't need to start from scratch.

### Deployment Using 63Klabs Atlantis

Deploy using the Atlantis CLI scripts from your DevOps SAM Config repo:

```bash
# Create the storage stack that will serve as the VideoOutputBucket
./cli/config.py storage PREFIX MY_STATIC_ASSETS
# CHOOSE TEMPLATE: template-storage-s3-oac-for-cloudfront.yml
# ADD TAG: AllowElementalMediaConvertOutput=true
# FROM THE OUTPUTS AFTER DEPLOY YOU WILL NEED FOR LATER:
# - BucketName
# - OriginBucketDomainForCloudFront

# Don't forget to deploy if you skipped deployment during config
./cli/deploy.py storage PREFIX MY_STATIC_ASSETS

# Create the Serverless Video Converter repo and seed it from the @chadkluck/serverless-video-converter
./cli/create_repo.py YOUR_GITHUB/YOUR_REPO_NAME --provider github --source https://github.com/chadkluck/serverless-video-converter

# OR, if using CodeCommit:
./cli/create_repo.py YOUR_REPO_NAME --provider codecommit --source https://github.com/chadkluck/serverless-video-converter

# Clone your repository and perform your first deployment AS-IS just to make sure it works
cd .. # Be sure to do this OUTSIDE of the DevOps SAM Config repo! Either from same command line or in a separate window
git clone YOUR_REPO_URL
cd YOUR_REPO_NAME

# checkout dev
git checkout dev
# inspect ./application-infrastructure/template-configuration.json and ensure the VideoOutputPrefix matches the output bucket prefix path (Leave VideoOutputBucket as that will be brought in from the pipeline)
# If you make any changes, ensure you commit and push the changes back to dev (however, try a first-time deploy as-is to make troubleshooting easier)

# You must merge dev into test before creating the pipeline (so it has something to deploy)
git checkout test
git merge dev
git push

# Create the test environment and deploy
# Go back to your DevOps SAM Config repo
cd ../YOUR_DEVOPS_SAM_CONFIG_REPO
./cli/config.py pipeline PREFIX YOUR_PROJECT_NAME test
# choose the template-pipeline.yml template when asked
# Follow the prompts (for S3StaticHostBucket you will use the bucket name of your Output bucket)

# Don't forget to deploy if you skipped deployment during config
./cli/deploy.py pipeline PREFIX YOUR_PROJECT_NAME test

# After it is created you will have a chance to deploy right away or do it later using the deploy.py command.
# Once deployed, test it out with a SHORT 30 to 60 second video:
cd ../SOME_DIR_WITH_A_SHORT_30_SEC_VIDEO
aws s3 cp test-video-file.mp4 s3://VIDEO_SOURCE_BUCKET/uploads/

# Because the bucket uses OAC for security, you will need a cloudfront distribution
# A custom domain record in Route 53 is optional, you can just use the CloudFront distribution url for testing
cd ../YOUR_DEVOPS_SAM_CONFIG_REPO
./cli/config.py network PREFIX YOUR_PROJECT_NAME test
# choose the template-network-route53-cloudfront-s3-apigw.yml template when asked
# Follow the prompts (You will need the OriginBucketDomainForCloudFront from the storage stack)

# Don't forget to deploy if you skipped deployment during config
./cli/deploy.py network PREFIX YOUR_PROJECT_NAME test
```

That's it! Now check the pipeline and CloudFormation progress in the console!

When you are confident with the way the application performs, you can set up a production instance that deploys from the `main` branch. Just replace `test` with `prod` in the above `config.py` and `deploy.py` commands.

### Deployment Without 63Klabs Atlantis

You will have to have a firm understanding of multi-stack, micro-service architecture as well as permissions and template configuration.

If this is your first time deploying to AWS, or deployments have been difficult to manage in the past and you are looking into automating some of your tasks, please look at 63Klabs Atlantis. (If you traditionally deploy applications through the Web Console, PLEASE look into Atlantis or at least Infrastructure as Code! I have many, many [tutorials to get you started](https://github.com/63Klabs/atlantis-tutorials) deploying production-ready applications!)

If you have a process that works or are using Terraform or other workflow to manage your deployments, then modify the template and function to suit your needs. You can use the template and configurations as guides.

## Checking Events

Of course, in the end if everything works right, you should soon be able to check the MediaConvert queue and subsequently the Output bucket for your video.

However, the process doesn't complete in a matter of seconds, and if there are issues you will be waiting for a long time.

To find if an S3 event triggered, you have several methods available depending on your setup and monitoring needs:

### 1. Check S3 Event Notifications Configuration

First, verify if you have S3 event notifications configured:

1. Go to the Amazon S3 console
2. Navigate to your bucket
3. Click the Properties tab
4. Look for the Event notifications section
5. Check if you have any event notification configurations set up

### 2. Monitor Event Destinations

If you have S3 event notifications configured correctly, check the destination Lambda function:

- Check CloudWatch Logs for your Lambda function
- Look for execution logs that indicate the function was triggered
- Review the function's invocation metrics in the Lambda console

### 3. Use CloudWatch Monitoring

You can monitor S3 events through CloudWatch:

- Check CloudWatch metrics for your S3 bucket
- Look for request metrics and data transfer metrics
- Set up CloudWatch alarms for specific S3 activities

### 4. Review CloudTrail Logs

For comprehensive event tracking:

- Enable AWS CloudTrail data events for your S3 bucket
- Review CloudTrail logs in CloudWatch Logs or S3
- Look for specific API calls like `GetObject`, `PutObject`, `DeleteObject`
- Set up CloudWatch metric filters to monitor specific S3 activities

### 5. Troubleshooting S3 Event Notifications

If events aren't triggering as expected:

- Verify Configuration:
   - Check prefix and suffix settings in your event notification
   - Ensure object keys match your naming guidelines
   - Confirm special characters are URL-encoded
- Check Permissions:
   - For Lambda: Ensure the resource-based policy allows S3 to invoke the function
- Timing Considerations:
   - S3 event notifications usually deliver within seconds but can take up to 1 minute
   - Events are delivered at least once but may arrive out of order or as duplicates

### 6. Test Your Setup

You can test if events are working by:

- Uploading a test file to your S3 bucket
- Performing the action that should trigger the event
- Checking your configured destinations for the notification

Remember that S3 supports various event types including object creation. Make sure your notification configuration includes the specific event types you want to monitor.

## Configuration

The application can be configured through parameters in the CloudFormation template:

- VideoOutputBucket: S3 bucket where transcoded videos will be stored
- VideoOutputPrefix: S3 object prefix (folder path) within the output bucket

The other parameters are standard for Atlantis templates so you can gather more info from the tutorials and documentation.

### Configuring Video Output Formats

The video output formats and resolutions are defined within the Lambda function code ([`job.json`](./application-infrastructure/src/job.json)). You can modify the job settings to suit your requirements. Refer to the [AWS Elemental MediaConvert documentation](https://docs.aws.amazon.com/mediaconvert/latest/ug/what-is.html) for details on job settings and configurations.

The following formats are currently in `job.json`:

- HLS
   - SD
   - 720p
   - 1080p
   - 4K
- MP4
   - SD
   - 720p
   - 1080p
   - 4K
- Thumbnails (.jpg)
   - 1280 x 720
   - 1920 x 1080

These outputs expect a 4K video with an aspect of 9:16 uploaded. The script does not check the resolution or aspect of uploaded videos. You will need to add that in if you require it, or prevent videos that do not meet requirements from being uploaded.

> Note: If you do not require 4K video outputs (or SD, etc), then you can remove them from the job specification as it will save you money.

### Handle Multiple VideoOutputBuckets

You can specify an output bucket on a per-video basis by using S3 object tags. The Lambda function can be modified to read the `VideoOutputBucket` tag from the uploaded video and use that as the `VideoOutputBucket` for the MediaConvert job.

```bash
aws s3 cp large-video-file.mp4 s3://VIDEO_SOURCE_BUCKET/uploads/ --tagging "VideoOutputBucket=bucketname"
```

> Note: Before the Lambda function will recognize a `VideoOutputBucket` in a tag, it MUST be passed as a value to the `VideoOutputBucket` parameter when the application is deployed. Also, the _OUTPUT BUCKET_ MUST have the tag key `AllowElementalMediaConvertOutput` with value `true`

For this to work, when creating the pipeline, do not set the `S3StaticHostBucket` parameter. Instead, set the `VideoOutputBucket` parameter directly in the `application-infrastructure/template-configuration.json` to a comma separated value listing each of the bucket names.

```yaml
{
  "Parameters": {
    "VideoOutputBucket": "bucket-name-one,bucket-name-two,bucket-name-3",
    "VideoOutputPrefix": "/$STAGE_ID$/public/videos/"
  }
}
```

While `VideoOutputBucket` is a comma separated list, `VideoOutputPrefix` is not. You will either need to modify the code or deploy separate instances in order to accommodate different output paths. When using the Atlantis developer platform for S3 buckets fronted by the CloudFront CDN, `$STAGE_ID$/public` is the standard prefix path. Changing this can cause issues when used with other Atlantis projects. You can change `videos` to whatever you want.

## Extending

This application can be extended in many ways by making it part of a chain of micro-services:

- Add additional processing steps using AWS Step Functions to add the formats to DynamoDB for creating an API to query the videos and available formats.
- Integrate with AWS Rekognition to analyze video content for moderation or metadata tagging.
- Integrate with AWS Transcribe to generate captions automatically.

When extending, it is important to maintain separation of concerns. Think of separate micro-services in a chain, each performing ONE duty. Use event driven architecture and step functions to orchestrate processing. Implement automation and checks such as not submitting a video with no audio, or only orchestral music, to Transcribe. Ensure there are places where a human can verify, intervene, or approve (step functions are great for this) to prevent unnecessary processing.

[Ideas](./docs/README-Ideas-For-Extending.md)

## AI Context

See [AI_CONTEXT.md](AI_CONTEXT.md) for important context and guidelines for AI-generated code in this repository.

The context file is also helpful (and perhaps essential) for HUMANS developing within the application's structured platform as well.

## Author

This application was developed by Chad Kluck (https://chadkluck.me) and is provided as open source under the MIT License. Feel free to use and modify it as needed.
