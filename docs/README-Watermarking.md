# Adding Water Marking to job.json

To add watermarking support to the MediaConvert job configuration, you will need to modify the `job.json` file used in your application infrastructure. Below are the steps to include watermarking in the MediaConvert job settings.

Add an `ImageInserter` to each `VideoDescription`in your outputs where you want the watermark.

Here's the minimal addition:

```json
"VideoDescription": {
  "Width": 1920,
  "Height": 1080,
  "ImageInserter": {
    "InsertableImages": [
      {
        "ImageX": 10,
        "ImageY": 10,
        "Layer": 1,
        "Opacity": 80,
        "ImageInserterInput": "s3://YOUR-WATERMARK-BUCKET/watermark.png"
      }
    ]
  },
  "CodecSettings": {
    // ... existing codec settings
  }
}
```

Make sure to replace `s3://YOUR-WATERMARK-BUCKET/watermark.png` with the actual S3 path where your watermark image is stored.

The watermark image should be:

- PNG format with transparency
- Stored in an S3 bucket accessible by your `MediaConvertRole`
- Sized appropriately for your video resolution

You'll also need to update your `MediaConvertRole` permissions to access the watermark bucket:

```yaml
- Sid: AccessToWatermarkBucket
  Action:
  - s3:GetObject
  Effect: Allow
  Resource: "arn:aws:s3:::YOUR-WATERMARK-BUCKET/*"
```

Make sure to replace `YOUR-WATERMARK-BUCKET` with the actual name of your S3 bucket containing the watermark image.

You can also add it as a parameter to be set when you deploy your application stack and as an environment variable to your Lambda function (maximum reusability).
