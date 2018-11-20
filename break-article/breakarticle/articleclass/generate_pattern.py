#from breakarticle.model.svs import Platforms, Devices
import random
import requests
import datetime
import logging
import json


# auto generate pattern from DPI team
class GeneratePattern:

    def __init__(self):
        # Required information for query DPI to generate pattern
        self.vendor_name = "ATOM"
        self.callback_url = "http://ts-monitor.atom.trendmicro.com:8880/v0/hips/dpi/callback2"
        self.query_pattern_url = "https://10.205.16.170/atom-api/public/v2/query"
        self.package_pattern_url = "https://10.205.16.170/atom-api/public/v2/pattern"
        self.pattern_info = {"SecurityList": {"a_security_list": [], "i_total_list": ""},
                             "SigInfo": {"s_sig_name": "", "s_date": "", "s_callback_uri": "", "s_project_code": "",
                                         "s_customer": "", "i_sig_ver_major": "", "i_sig_ver_minor": "",
                                         "i_sig_request": ""},
                             "HWInfo": {"s_hw_name": "", "i_hw_mem_usage": "", "i_hw_mem": ""}}

    def constitute_info(self, device_id, query_key_list, request_action=1):
        try:
            # construct SecurityList list
            for query_key in query_key_list:
                self.pattern_info["SecurityList"]["a_security_list"].append({"s_security_name": query_key,
                                                                             "i_state": 0})
            self.pattern_info["SecurityList"]["i_total_list"] = int(len(self.pattern_info["SecurityList"]
                                                                        ["a_security_list"]))
            # construct SigInfo list
            # The DPI pattern filename: "s_customer"-"i_sig_ver_major"."i_sig_ver_minor".zip
            # the i_sig_ver_minor number need up to 100
            self.pattern_info["SigInfo"]["s_sig_name"] = self.vendor_name
            self.pattern_info["SigInfo"]["s_date"] = str(datetime.datetime.now())
            self.pattern_info["SigInfo"]["s_callback_uri"] = self.callback_url
            self.pattern_info["SigInfo"]["s_project_code"] = self.vendor_name
            self.pattern_info["SigInfo"]["s_customer"] = self.vendor_name
            self.pattern_info["SigInfo"]["i_sig_ver_major"] = int(random.randint(1, 99))
            self.pattern_info["SigInfo"]["i_sig_ver_minor"] = int(random.randint(100, 500))
            self.pattern_info["SigInfo"]["i_sig_request"] = int(request_action)

            # construct HWInfo list
            self.pattern_info["HWInfo"]["i_hw_mem_usage"] = int(1024)
            try:
                device_info = Devices.query.filter_by(device_guid=str(device_id)).first()
                platform_info = Platforms.query.filter_by(platform_id=int(device_info.platform_id)).first()
                self.pattern_info["HWInfo"]["s_hw_name"] = str(platform_info.platform_name)
                self.pattern_info["HWInfo"]["i_hw_mem"] = int(platform_info.memory_kb)
            except Exception as e:
                self.pattern_info["HWInfo"]["s_hw_name"] = str("Default_plattern")
                self.pattern_info["HWInfo"]["i_hw_mem"] = int(40960)
                logging.exception(e)
        except Exception as exc:
            logging.exception(exc)
            logging.debug("constitute security_key value was failed, DPI pattern info: {}".format(self.pattern_info))
            raise
        finally:
            pattern_info_json = json.dumps(self.pattern_info)
            logging.info("finally: json_str: {}".format(pattern_info_json))
            return pattern_info_json

    def request_pattern(self, pattern_info_json, request_action=1):
        payload = pattern_info_json
        headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache"
        }
        if request_action == 1:
            response = requests.request("POST", self.query_pattern_url, data=payload, headers=headers, verify=False)
        elif request_action == 2:
            response = requests.request("POST", self.package_pattern_url, data=payload, headers=headers, timeout=2, verify=False)
        if response.status_code == 200:
            return response
        else:
            logging.debug('DPI generated pattern was failed, status_code {}'.format(response.status_code))
