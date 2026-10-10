# TODO

[X] Separate buckets for each video based on object tag
[X] Test with Storage and Network stacks, update documentation
[ ] Break out the job.json so that each video can receive it's own output specifications
[ ] Improve logging and monitoring
[ ] Add CloudWatch Dashboard for monitoring
[ ] Add dry run
[ ] Add SNS topic for job completion notification
[ ] Add CloudWatch Alarm for failed jobs
[ ] Add check in Lambda function to ensure video has not already been processed
[ ] Add check in lambda function for closed caption files and if exists submit along with job? Does this embed as subtitles? The web video javascript may have it's own method
