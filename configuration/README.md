# dell-obs-knative-bucket-notification configuration
----------------------------------------------------------------------------------------------
dell-obs-knative-bucket-notification is a PYTHON based POC that is intended to be deployed to 
Knative as a service that listens for bucket event notifications from an ObjectScale cluster and 
then looks for image files, extrtacts the image data from the source S3 bucket, create thumbnails
for the images and then store the thumbnails in a target S3 bucket.

We've provided a sample configuration file:

- dell_obs_knative_bucket_notification.sample: Change file suffix from .sample to .json and configure as needed
  This contains the tool configuration for Flask, S3, and Thumbnail processing.
  
  BASE:
  logging_level - The default is "info" but it can be set to "debug" to generate a LOT of details
  flask_port - This is the port that the Flask service will listen on.  Default is "5002"


  DELL_S3_CONNECTION:

  - protocol - This can be either "https" or "http"
  - host - This is the IP address of FQDN of a Dell ObjectScale ObjectStore S3 Endpoint
  - port - This is the port of the Dell ObjectScale ObjectStore S3 Endpoint
  - s3AccessKey - This is the access key of the ObjectScale IAM Account User
  - s3SecretKey - This is the secret key of the ObjectScale IAM Account User
  - connectTimeout - This is the connection timeout in seconds 
  - readTimeout - This is the read timeout in seconds

  THUMBNAIL_GENERATION:

  - S3EventSourceBucket = This is the bucket that generated the events
  - thumbnailS3Bucket - This is the bucket that the generated image thumbnails will be stored in
  - thumbnailSize -  This is the size of the thumbnail that will be generated
