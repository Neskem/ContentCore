import botocore
import os
from flask import current_app
from breakarticle.exceptions import AtomAddPatternFailedError


def upload_pattern(vendor_key_id, device_id, tmp_file_obj):
    if os.path.isfile(tmp_file_obj.tmp_pattern_zip_path) is False:
        raise AtomAddPatternFailedError("{} is not a file".format(tmp_file_obj.tmp_pattern_zip_path))

    pattern_hash = tmp_file_obj.pattern_zip_hash
    with open(tmp_file_obj.tmp_pattern_zip_path, "rb") as f:
        upload_object_key = get_object_key(vendor_key_id, device_id, pattern_hash)
        try:
            res = current_app.s3client.put_object(
                Bucket=current_app.config['AWS_S3_HIPS_BUCKET_ID'],
                Body=f,
                Key=upload_object_key
            )
            return upload_object_key, res
        except botocore.exceptions.ClientError as e:
            raise e


def get_object_key(vendor_key_id, device_id, pattern_hash):
    """This is for hips bucket"""
    return '{0}/{1}/{2}'.format(
        vendor_key_id,
        device_id,
        pattern_hash)
