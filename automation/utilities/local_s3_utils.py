import boto3
from botocore.credentials import Credentials


class LocalS3Session(object):
    """
    Ensures that the local s3 service is used when
    setup as the default boto3 Session
    Based on localstack_client/session.py
    """
    def __init__(self, aws_access_key_id='accesskey', aws_secret_access_key='secretkey',
                 aws_session_token='token', region_name='us-east-1', endpoint_url='http://localhost:4572',
                 botocore_session=None, profile_name=None, localstack_host=None):
        self.env = 'local'
        self.session = boto3.session.Session()
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        self.region_name = region_name
        self.endpoint_url = endpoint_url

    def resource(self, service_name, **kwargs):
        return self.session.resource(service_name,
                                     endpoint_url=self.endpoint_url,
                                     aws_access_key_id=self.aws_access_key_id,
                                     aws_secret_access_key=self.aws_secret_access_key,
                                     region_name=self.region_name, verify=False)

    def get_credentials(self):
        return Credentials(access_key=self.aws_access_key_id,
                           secret_key=self.aws_secret_access_key,
                           token=self.aws_session_token)

    def client(self, service_name, **kwargs):
        return self.session.client(service_name, endpoint_url=self.endpoint_url,
                                   aws_access_key_id=self.aws_access_key_id,
                                   aws_secret_access_key=self.aws_secret_access_key,
                                   region_name=self.region_name, verify=False)

    def resource(self, service_name, **kwargs):
        return self.session.resource(service_name,
                                     endpoint_url=self.endpoint_url,
                                     aws_access_key_id=self.aws_access_key_id,
                                     aws_secret_access_key=self.aws_secret_access_key,
                                     region_name=self.region_name, verify=False)


def local_s3_bucket():
    """Use localstack as our local S3 service."""
    # Make boto3 use our localstack S3 endpoint
    boto3.DEFAULT_SESSION = LocalS3Session()
    # Create a local bucket
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('localstack-foo')
    bucket.create()
    return 'localstack-foo'


def download_s3_directory(dir, destination='/tmp', bucket='your_bucket'):
    client = boto3.client('s3')
    resource = boto3.resource('s3')
    paginator = client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=dir):
        if result.get('CommonPrefixes') is not None:
            for subdir in result.get('CommonPrefixes'):
                download_s3_directory(
                    subdir.get('Prefix'), destination, bucket)
        for file in result.get('Contents', []):
            dest_pathname = os.path.join(destination, file.get('Key'))
            if not os.path.exists(os.path.dirname(dest_pathname)):
                os.makedirs(os.path.dirname(dest_pathname))
            resource.meta.client.download_file(
                bucket, file.get('Key'), dest_pathname)
