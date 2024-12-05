import boto3
from botocore.client import Config
from django.conf import settings


class S3Helper():
    """
    Utility that wraps download from S3
    """
    s3client = None

    @classmethod
    def get_client(cls):
        if not cls.s3client:
            cfg = Config(signature_version='s3v4')
            cls.s3client = boto3.client('s3', settings.AWS_REGION, config=cfg)
        return cls.s3client

    def get_presigned_urls(self, attachment):
        if attachment is None:
            return attachment
        s3 = S3Helper.get_client()
        return s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': settings.ATTACHMENT_BUCKET, 'Key': attachment},
            ExpiresIn=604800  # Expires in 1 weeks
        )

    def delete_s3_object(self, attachment):
        s3 = S3Helper.get_client()
        response =  s3.delete_object(Bucket=settings.ATTACHMENT_BUCKET, Key=attachment)
        print(response, "response")


# this keeps things backward compatible, without replacing usage
s3h = S3Helper()
s3_get_presigned_urls = s3h.get_presigned_urls
s3_delete_file = s3h.delete_s3_object


def chunks(l, chunk_size):
    """
    Yield successive n-sized chunks from
    l which is a generator
    """
    result = []
    for elem in l:
        if len(result) < chunk_size:
            result.append(elem)
        else:
            yield result
            result = [elem]
    yield result
    result = []
