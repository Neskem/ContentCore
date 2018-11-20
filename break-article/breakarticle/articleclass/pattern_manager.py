from flask import has_request_context
from breakarticle.exceptions import AtomAddPatternFailedError
from breakarticle.exceptions import AtomInvalidFilenameError
from breakarticle.exceptions import AtomInvalidFileCountError
from werkzeug.utils import secure_filename
from breakarticle.definition import PATTERN_TMP_FOLDER
from breakarticle.helper import pg_add_wrapper
from breakarticle.model import db
from breakarticle.atomlogging import request_id

import requests
import datetime
import logging
import os
import uuid
import zipfile
import shutil
import json
import hashlib


def init_pattern(device_id):
    new_init_pattern = DevicePatternStatus(device_id=device_id, pattern_status='done')
    pg_add_wrapper(new_init_pattern)


def add_pattern(device_id, pattern_hash):
    # Add new pattern first
    logging.info("Insert pattern information to database: device_id: {}, pattern_hash: {}"
                 .format(device_id, pattern_hash))
    new_upload_pattern = UploadPattern(device_id=device_id, pattern_hash=pattern_hash)
    pg_add_wrapper(new_upload_pattern)


def deploying_pattern(device_id, upload_pattern_id):
    db.session.query(DevicePatternStatus).filter_by(device_id=device_id).update({
        'pattern_status': 'pending',
        'selected_pattern_id': upload_pattern_id,
        'deployed_time': datetime.datetime.now()
    })
    db.session.commit()
    logging.info("Louis_deploy_pattern, device_id: {}, upload_pattern_id: {}".format(device_id, upload_pattern_id))


def validate_pattern_filename(filename):
    import re
    invalid_fragment = []
    prog = re.compile("(\.){2,}|([/`=!@$%^&~*+])", flags=re.IGNORECASE)
    for m in prog.finditer(filename):
        logging.error("Invalid pattern filename fragment : %s", m.group(0))
        invalid_fragment.append(m.group(0))
    if len(invalid_fragment) > 0:
        raise AtomInvalidFilenameError
    return True


def validate_ext_filename(filename, allowed_exts):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_exts


def handle_unique_file(myzip, handle_filename, tmp_handle_path):
    myzip.extract(handle_filename, path=PATTERN_TMP_FOLDER)
    original_path = os.path.join(PATTERN_TMP_FOLDER, handle_filename)
    shutil.move(original_path, tmp_handle_path)


def notify_devices_mqtt(vendor_key_id, devices_list, retain=False):
    publish_ts_uuid = uuid.uuid4()
    mqtt_content = {"mqtt_topics": [], "mqtt_message": {"vp_hash": []},
                    "is_retain": retain, "publish_ts": str(publish_ts_uuid)}

    mqtt_topics_list = []
    vp_hash_list = []
    for device_id in devices_list:
        mqtt_topics = 'atom2/hips/device/atom2|' + vendor_key_id + '|' + device_id
        mqtt_topics_list.append(mqtt_topics)
        device_info = DevicePatternStatus.query.filter_by(device_id=device_id).first()
        device_pattern_info = UploadPattern.query.filter_by(id=device_info.selected_pattern_id).first()
        vp_hash_list.append(device_pattern_info.pattern_hash)

    mqtt_content['mqtt_topics'] = mqtt_topics_list
    mqtt_content['mqtt_message']['vp_hash'] = vp_hash_list
    logging.info("notify_device_gateway: mqtt_content: {}".format(mqtt_content))

    # TODO Change: Modify and confirm URI with device gateway
    # req_id = request_id() if has_request_context() else uuid.uuid4()
    # headers = {
    #    'X-ATOM-REQUEST-ID': str(req_id)
    # }
    # url_prefix = current_app.config['GRID_URI']
    # url_prefix = "http://localhost:8700"
    # url = '{url_prefix}/v0/dgw/internal/mqtt-publish'.format(url_prefix=url_prefix)
    # r = requests.post(url, data=mqtt_content, headers=headers, timeout=2)
    # if r.status_code == 200:
    #    return True
    # else:
    #    logging.error('notify_device_gateway_status returns %s: %s', r.status_code, r.text)
    #    return False


class TmpZippedPattern:

    def __init__(self, in_file):
        self.in_file = in_file
        self.filename = secure_filename(in_file.filename)
        self.upload_complete = False
        self.pattern_unique_filename = uuid.uuid4()
        self.meta_unique_filename = uuid.uuid4()
        self.md5_unique_filename = uuid.uuid4()
        self.zip_unique_filename = uuid.uuid4()
        self.tmp_pattern_path = os.path.join(PATTERN_TMP_FOLDER, str(self.pattern_unique_filename))
        self.tmp_meta_path = os.path.join(PATTERN_TMP_FOLDER, str(self.meta_unique_filename))
        self.tmp_md5_path = os.path.join(PATTERN_TMP_FOLDER, str(self.md5_unique_filename))
        self.tmp_pattern_zip_path = os.path.join(PATTERN_TMP_FOLDER, str(self.zip_unique_filename))

        # Archived filenames to be used latter
        self.real_pattern_filename = ''
        self.meta_filename = ''
        self.md5_pattern_filename = ''
        self.pattern_zip_hash = ''

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        if os.path.isfile(self.tmp_pattern_zip_path) is True:
            os.unlink(self.tmp_pattern_zip_path)
        if os.path.isfile(self.tmp_pattern_path) is True:
            os.unlink(self.tmp_pattern_path)
        if os.path.isfile(self.tmp_meta_path) is True:
            os.unlink(self.tmp_meta_path)
        if os.path.isfile(self.tmp_md5_path) is True:
            os.unlink(self.tmp_md5_path)

    def validate_archive(self):
        try:
            with zipfile.ZipFile(self.in_file, 'r') as myzip:
                zip_info_list = myzip.infolist()

                # zip file including: *.trf, *.md5, *.json
                if len(zip_info_list) < 3:
                    raise AtomInvalidFileCountError

                for info in zip_info_list:
                    if validate_ext_filename(info.filename, 'json'):
                        if 'meta_en-US' in info.filename:
                            self.meta_filename = info.filename
                            handle_unique_file(myzip, self.meta_filename, self.tmp_meta_path)
                    elif validate_ext_filename(info.filename, 'trf'):
                        self.real_pattern_filename = info.filename
                        handle_unique_file(myzip, self.real_pattern_filename, self.tmp_pattern_path)
                    elif validate_ext_filename(info.filename, 'md5'):
                        self.md5_pattern_filename = info.filename
                        handle_unique_file(myzip, self.md5_pattern_filename, self.tmp_md5_path)

                if self.real_pattern_filename == '' or self.meta_filename == '' or self.md5_pattern_filename == '':
                    raise AtomAddPatternFailedError

            with open(self.tmp_meta_path, "rb") as f:
                data = json.load(f)

            # filter "IPSCategory" and "IPSInfo" from meta.json file
            meta_json = {"IPSCategory": data.get("IPSCategory"), "IPSInfo": data.get("IPSInfo")}

            with open(self.tmp_meta_path, 'w') as f:
                json.dump(meta_json, f)

            with zipfile.ZipFile(self.tmp_pattern_zip_path, 'w') as zf:
                zf.write(self.tmp_pattern_path, 'trf')
                zf.write(self.tmp_meta_path, 'meta')
                zf.write(self.tmp_md5_path, 'md5')

            block_size = 65536
            hash_method = hashlib.sha1()
            with open(self.tmp_pattern_zip_path, 'rb') as zip_file:
                buf = zip_file.read(block_size)
                while len(buf) > 0:
                    hash_method.update(buf)
                    buf = zip_file.read(block_size)
            self.pattern_zip_hash = hash_method.hexdigest()
        except zipfile.BadZipfile:
            logging.debug('A bad ZIP file %s', self.in_file.filename)
            raise
        except zipfile.LargeZipFile:
            logging.error('ZIP64 is not supports. Please enable ZIP64 feature.')
            raise
