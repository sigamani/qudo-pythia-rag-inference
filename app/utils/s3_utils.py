import boto3
import s3fs
import json


def get_s3_resource():
    # Create S3 client
    s3 = boto3.resource("s3")
    return s3


class S3Utils:
    def __init__(self, bucket, environ):
        self.bucket = bucket
        self.environ = environ
        self.s3 = boto3.resource('s3')
        self.s3_client = boto3.client('s3')
        self.s3_check = s3fs.S3FileSystem()

    def is_valid_uri(self, filepath):
        filepath = f's3://{self.bucket}/{filepath}'
        return self.s3_check.exists(filepath)

    def read_file(self, filepath):
        content_obj = self.s3.Object(self.bucket, filepath)
        content = content_obj.get()['Body'].read()
        response = json.loads(content)
        return response

