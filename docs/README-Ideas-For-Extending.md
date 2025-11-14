# Ideas for Extending

## Make Part of a Chain

This solution is designed to be a single micro-service in a chain of services. You can extend this solution by adding additional Lambda functions and Step Functions to create a processing pipeline. For example, you could add a transcription step that upon upload, if the video object is marked with a `transcribe` tag it will send a job request to Amazon Transcribe. Same with Rekognition.

## Watermarking

You can add watermarking to the MediaConvert job by modifying the `job.json` file used in the Lambda function. See the [Adding Water Marking to job.json](./docs/README-Watermarking.md) documentation for details on how to implement watermarking in your MediaConvert jobs.

## Custom Job Settings

Right now there is only one setting, which means all videos uploaded need to be 4K with a widescreen (16:9) aspect ratio.

You could tag the video with additional tags (similar to tagging with the output bucket) to direct different settings. Furthermore, instead of using the CLI to upload videos and manually tagging through `--tagging KEY=VALUE` pairs, you could create an interface to upload and check boxes for the formats wanted, and even inspect the video at upload to determine ratio and max resolution.

For more information on job settings, see [AWS documentation for Job Settings](https://docs.aws.amazon.com/solutions/latest/video-on-demand-on-aws-foundation/job-settings-file.html).

For even more, see [AWS documentation for Job Settings file examples](https://docs.aws.amazon.com/mediaconvert/latest/ug/example-job-settings.html).

## Captions

MediaConvert does accept caption files as part of the job submission. You will need to ensure the caption file is available prior to submitting the job to MediaConvert. This can be baked into a preprocess. For example, the S3 triggers only on `.mp4` file uploads (you could include additional video formats as well). You could have a previous process generate a transcript and place the caption file in the same `VideoSourceBucket` prior to uploading the video file. The Lambda function can then receive the event for the video file and check to see if there is a companion transcript. If there is then submit that with the job.
