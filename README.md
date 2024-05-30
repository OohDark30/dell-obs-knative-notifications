# dell-obs-knative-notifications
----------------------------------------------------------------------------------------------
dell-obs-knative-bucket-notification is a PYTHON based POC that is intended to be deployed to 
Knative as a service that listens for bucket event notifications from an ObjectScale cluster and 
then looks for image files, extrtacts the image data from the source S3 bucket, create thumbnails
for the images and then store the thumbnails in a target S3 bucket.
