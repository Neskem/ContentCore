import mysql.connector
import logging
from breakarticle.config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWD, MYSQL_DATABASE
from breakarticle.exceptions import BreakPartnerError

logger_name = "logger_admin"
logger = logging.getLogger(logger_name)


class PartnerSetting:

    def __init__(self, partner_id):
        self.partner_id = str(partner_id)
        self.mydb = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            passwd=MYSQL_PASSWD,
            database=MYSQL_DATABASE
        )

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        self.mydb.close()

    def validate_partner(self):
        try:
            self.validate_partner_query_str = "SELECT * FROM alliance.app_partner where partnerId=" \
                                              + str("'") + self.partner_id + str("'")
            partnerdb = self.mydb.cursor()
            partnerdb.execute(self.validate_partner_query_str)
            partnerdb_result = partnerdb.fetchall()
            if partnerdb_result:
                logger.debug("This partner was registered in partner system : {}".format(self.partner_id))
                return True
            else:
                logger.debug("This partner was not registered in partner system : {}".format(self.partner_id))
                return False
        except:
            logger.debug("Can't search partner was registered or system has happen error, partner_id: {}".format(self.partner_id))
            raise BreakPartnerError

    def get_website_id(self):
        try:
            self.get_partner_name_query_str = "SELECT username FROM alliance.app_partner where partnerId=" \
                                              + str("'") + self.partner_id + str("'")
            partnerdb = self.mydb.cursor()
            partnerdb.execute(self.get_partner_name_query_str)
            partner_name = partnerdb.fetchall()
            str_partner_name = str(partner_name)
            self.get_website_id_query_str = "SELECT id FROM alliance.app_website where name=" \
                                 + str("'") + str_partner_name.split("'")[1] + str("'")
            partnerdb.execute(self.get_website_id_query_str)
            website_id = partnerdb.fetchall()
            if website_id:
                str_website_id = str(website_id)
                int_website_id = str_website_id.strip('[(,)]')
                logger.debug("This partner of website id is: {}".format(int_website_id))
                return int_website_id
            else:
                logger.debug("Can't find this partner of website id: {}".format(website_id))
                return False
        except:
            logger.debug("Can't search partner was registered or system has happen error, partner_id: {}".format(self.partner_id))
            raise BreakPartnerError

    def get_partner_config(self, website_id_res):
        """
        partner system URL: www.5438.com.tw (website id = 3357)
        Debug query string from database:
        self.get_partner_config_query_str = "SELECT * FROM alliance.app_websiteconfig where website_id='3357'"
        """
        try:
            self.get_partner_config_query_str = "SELECT * FROM alliance.app_websiteconfig where website_id=" + website_id_res
            partnerdb = self.mydb.cursor()
            partnerdb.execute(self.get_partner_config_query_str)
            partner_config_res = partnerdb.fetchall()
            logger.debug("partner_config_res : {}".format(partner_config_res))
            if partner_config_res:
                partner_config = {}
                partner_config_value = []
                partner_config_regex = {}
                partner_config_regex_value = []
                for row in partner_config_res:
                    if row[1] == 'regex':
                        partner_config_regex_value.append(str(row[2]))
                        partner_config_regex.update({row[7]: partner_config_regex_value})
                        partner_config.update({row[1]: partner_config_regex})
                    else:
                        if row[1] in partner_config.keys():
                            partner_config_value.append(partner_config[row[1]])
                            partner_config_value.append(str(row[2]))
                            partner_config.update({row[1]: partner_config_value})
                        else:
                            partner_config.update({row[1]: str(row[2])})
                    logger.debug("row : {}".format(row))
                logger.debug("This partner configure : {}".format(partner_config))
                return partner_config
            else:
                logger.debug("Can't find this partner of partner configure website_id: {}".format(website_id_res))
                return False
        except:
            logger.info("Can't find this partner of partner configure or system has happen error, website_id: {}".format(website_id_res))
            raise BreakPartnerError
