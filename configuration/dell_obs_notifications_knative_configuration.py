"""
DELL Object Notifications on Knative Module.
"""
import logging
import os
import json
import numbers

# Constants
BASE_CONFIG = 'BASE'                                          # Base Configuration Section
DELL_S3_CONNECTION = 'DELL_S3_CONNECTION'                     # Dell OBS S3 Configuration Section
THUMBNAIL_GENERATION = 'THUMBNAIL_GENERATION'                 # Thumbnail Configuration Section


class InvalidConfigurationException(Exception):
    pass


class DellObsKnativeConfiguration(object):
    def __init__(self, config, tempdir):

        if config is None:
            raise InvalidConfigurationException("No file path to the DELL Object Notifications Knative Module "
                                                "configuration provided")

        if not os.path.exists(config):
            raise InvalidConfigurationException("The DELL Object Notifications Knative Module configuration "
                                                "file path does not exist: " + config)
        if tempdir is None:
            raise InvalidConfigurationException("No path for temporary file storage provided")

        # Store temp file storage path to the configuration object
        self.tempfilepath = tempdir

        # Attempt to open configuration file
        try:
            with open(config, 'r') as f:
                parser = json.load(f)
        except Exception as e:
            raise InvalidConfigurationException("The following unexpected exception occurred in the "
                                                "Object Notifications Knative Module attempting to parse "
                                                "the configuration file: " + e.message)

        # We parsed the configuration file now lets grab values
        self.dells3connection = parser[DELL_S3_CONNECTION]
        self.thumbnailgeneration = parser[THUMBNAIL_GENERATION]

        # Set logging level and Flask port
        logging_level_raw = parser[BASE_CONFIG]['logging_level']
        self.logging_level = logging.getLevelName(logging_level_raw.upper())
        self.flask_port = parser[BASE_CONFIG]['flask_port']

        # Validate logging level
        if logging_level_raw not in ['debug', 'info', 'warning', 'error']:
            raise InvalidConfigurationException(
                "Logging level can be only one of ['debug', 'info', 'warning', 'error']")

        # Validate Flask port
        if not self.flask_port:
            raise InvalidConfigurationException("The Flask port is not configured in the module configuration")

        # Validate Dell S3 connection details
        if not self.dells3connection['protocol']:
            raise InvalidConfigurationException("The Dell S3 Protocol is not configured in the module configuration")

        protocol = self.dells3connection['protocol']
        if protocol not in ['http', 'https']:
            raise InvalidConfigurationException("The Dell S3 Protocol can only be one of ['http', 'https']")

        if not self.dells3connection['host']:
            raise InvalidConfigurationException("The Dell S3 Host is not configured in the module configuration")

        if not self.dells3connection['port']:
            raise InvalidConfigurationException("The Dell S3 port is not configured in the module configuration")

        if not self.dells3connection['s3AccessKey']:
            raise InvalidConfigurationException("The Dell S3 Access Key is not configured in the module configuration")

        if not self.dells3connection['s3SecretKey']:
            raise InvalidConfigurationException("The Dell S3 Secrete Key is not configured "
                                                "in the module configuration")

        if not self.dells3connection['connectTimeout']:
            raise InvalidConfigurationException("The Dell S3 connection timeout is not configured in the module "
                                                "configuration")

        if not self.dells3connection['readTimeout']:
            raise InvalidConfigurationException("The Dell S3 read timeout is not configured in the module configuration")

        # Validate Image Thumbnail Generation Details
        if self.thumbnailgeneration['S3EventSourceBucket'] is None:
            raise InvalidConfigurationException("The S3 Event Source Image Bucket has not been set in the module "
                                                "configuration")
        if self.thumbnailgeneration['thumbnailS3Bucket'] is None:
            raise InvalidConfigurationException("The S3 bucket to use for Thumbnail Generation has not been set in "
                                                "the module configuration")
        if self.thumbnailgeneration['thumbnailSize'] is None:
            raise InvalidConfigurationException("The Thumbnail Size has not been set in the module configuration")


