import io
import json
import os
import traceback
import logging
import uuid

from flask import (
    request, Flask
)

from configuration.dell_obs_notifications_knative_configuration import DellObsKnativeConfiguration
from logger import dell_obs_logger
from s3 import GetConnection
from PIL import Image

# Constants
MODULE_NAME = "dell_obs_knative_event_notifications"  # Module Name
CONFIG_FILE = 'dell_obs_knative_notifications.json'  # Default Configuration File

# Globals
_configuration = None
_logger = None
_b_first_time = True
_s3_connection = None
_temp_file_path = None


# Dell OBS Knative Configuration
def dell_obs_knative_config(config, temp_dir):
    global _configuration
    global _logger
    global _temp_file_path

    try:
        # Load and validate module configuration
        _configuration = DellObsKnativeConfiguration(config, temp_dir)

        # Set global temp file dir
        _temp_file_path = temp_dir

        # Grab loggers and log status
        _logger = dell_obs_logger.get_logger(__name__, _configuration.logging_level)
        _logger.info(MODULE_NAME + '::dell_obs_knative_config()::We have configured logging level to: '
                     + logging.getLevelName(str(_configuration.logging_level)))
        _logger.info(MODULE_NAME + '::dell_obs_knative_config()::Configuring Dell OBS Notifications Knative Module '
                                   'complete.')
        return _configuration
    except Exception as e:
        _logger.error(MODULE_NAME + '::dell_obs_knative_config()::The following unexpected '
                                    'exception occurred: ' + str(e) + "\n" + traceback.format_exc())
        return None


def generate_s3_thumbnail(s3_connection, source_bucket, object_key, thumbnail_size, target_bucket):
    global _temp_file_path

    # split the object key to get the file name and extension
    file_parts = object_key.split('.')
    file_name = file_parts[0]
    file_extension = file_parts[1]

    # Get the object from the s3 bucket configured for the source bucket
    response = s3_connection.get_object(Bucket=source_bucket, Key=object_key)

    # Read the object
    image_data = response['Body'].read()

    # Create an image file with the image byte data
    try:
        image_stream = io.BytesIO(image_data)
        image = Image.open(image_stream)
        print(image.format, f"{image.size}x{image.mode}")

        if image.format not in ['JPEG', 'PNG', 'GIF', 'BMP', 'MPO']:
            print("Unsupported image format")
            return

        # If we have image data lets close the stream and the process the image data
        if image_stream is not None:

            # Let's create a temp file to store the image
            temp_file = os.path.abspath(os.path.join(_temp_file_path, str(uuid.uuid4())))

            # Create a thumbnail for the image and save it to a NamedTemporaryFile
            try:
                image.thumbnail(thumbnail_size)

                # Save base on image format
                if image.format == 'GIF':
                    temp_file = temp_file + ".gif"
                    image.save(temp_file)
                else:
                    if image.format == 'JPEG':
                        temp_file = temp_file + ".jpg"
                        image.save(temp_file)
                    else:
                        if image.format == 'PNG':
                            temp_file = temp_file + ".png"
                            image.save(temp_file)
                        else:
                            if image.format == 'BMP':
                                temp_file = temp_file + ".bmp"
                                image.save(temp_file)
                            else:
                                if image.format == 'MPO':
                                    temp_file = temp_file + ".jpg"
                                    image.save(temp_file)

                image_stream.close()

                # Write the thumbnail to s3 bucket configured as the target bucket
                with open(temp_file, "rb") as f:
                    s3_connection.put_object(
                        Bucket=target_bucket,
                        Body=f,
                        Key=file_name + "_thumbnail." + file_extension
                    )
            except OSError:
                print("cannot create thumbnail for", temp_file.name)
    except Exception as e2:
        print(MODULE_NAME + 'generate_s3_thumbnail::The following unexpected error occurred: ' + str(
            e2) + "\n" + traceback.format_exc())


# Flask Application
application = Flask(__name__)


@application.route('/', methods=['POST'])
def webhook():
    # Declare globals
    global _b_first_time
    global _configuration
    global _s3_connection

    # Handle POST request
    if request.method == 'POST':

        # If this is the first time we're receiving a POST request then we need to grab the s3 configuration
        # information and generate a connection
        if _b_first_time:
            # Grab the s3 configuration information
            s3endpoint = _configuration.dells3connection['protocol'] + "://" + _configuration.dells3connection[
                'host'] + ":" + _configuration.dells3connection['port']
            s3accesskey = _configuration.dells3connection['s3AccessKey']
            s3secretkey = _configuration.dells3connection['s3SecretKey']

            # Create boto3 s3 client
            _s3_connection = GetConnection.getConnection(s3endpoint, False, s3accesskey, s3secretkey)

            # Set the first time flag to false
            _b_first_time = False

        # Get Bucket Notification Event Data
        event_data = json.loads(request.data)

        # Extract the bucket and object key from the json event data
        event_bucket = event_data['Records'][0]['s3']['bucket']['name']
        event_object_key = event_data['Records'][0]['s3']['object']['key']

        # Test if the file is an image of type jpeg or png
        if event_object_key.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.mpo')):
            # Let's retrieve the image and generate a thumbnail
            generate_s3_thumbnail(_s3_connection, event_bucket, event_object_key, (128, 128),
                                  _configuration.thumbnailgeneration['thumbnailS3Bucket'])

            return ("Bucket Event Notification Successfully processed and image thumbnail generated for object: " +
                    event_object_key)

        return "Bucket Event Notification Successfully processed for object: " + event_object_key

    return "Failure"


@application.route('/', methods=['GET'])
def hello():
    return (b'Welcome to the Dell ObjectScale Bucket Notifications Sample for Knative!.  Perform a POST to this '
            b'endpoint to deliver a bucket event notification.')


if __name__ == '__main__':
    try:

        # Dump out application path
        currentApplicationDirectory = os.getcwd()
        configFilePath = os.path.abspath(os.path.join(currentApplicationDirectory, "configuration", CONFIG_FILE))
        temp_file_dir = os.path.abspath(os.path.join(currentApplicationDirectory, "temp"))

        # Create temp directory if it doesn't already exist
        if not os.path.isdir(temp_file_dir):
            os.mkdir(temp_file_dir)
        else:
            # The directory exists so lets scrub any temp files out that may be in there
            files = os.listdir(temp_file_dir)
            for file in files:
                os.remove(os.path.join(currentApplicationDirectory, "temp", file))

        print(MODULE_NAME + "::__main__::Current directory is : " + currentApplicationDirectory)
        print(MODULE_NAME + "::__main__::Configuration file path is: " + configFilePath)

        # Initialize configuration
        config = dell_obs_knative_config(configFilePath, temp_file_dir)
        if config is not None:
            print(MODULE_NAME + "::__main__::Dell OBS Knative Configuration complete.")
            # Run app
            application.run(debug=True, host='0.0.0.0', port=5002)

    except Exception as e:
        print(MODULE_NAME + '__main__::The following unexpected error occurred: ' + str(
            e) + "\n" + traceback.format_exc())
