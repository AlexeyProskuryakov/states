# coding=utf-8
import logging
import os
import sys

__author__ = 'alesha'


def module_path():
    if hasattr(sys, "frozen"):
        return os.path.dirname(
            sys.executable
        )
    return os.path.dirname(__file__)


SEC = 1
MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24
WEEK = DAY * 7
WEEK_DAYS = {0: "MO", 1: "TU", 2: "WE", 3: "TH", 4: "FR", 5: "SA", 6: "SU"}

log_file_f = lambda x: os.path.join(module_path(), (x if x else "") + 'result.log')
log_file = os.path.join(module_path(), 'result.log')
cacert_file = os.path.join(module_path(), 'cacert.pem')

logger = logging.getLogger()

logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s[%(levelname)s]%(name)s|%(processName)s(%(process)d): %(message)s')
formatter_process = logging.Formatter('%(asctime)s[%(levelname)s]%(name)s|%(processName)s: %(message)s')
formatter_human = logging.Formatter('%(asctime)s[%(levelname)s]%(name)s|%(processName)s: %(message)s')

sh = logging.StreamHandler()
sh.setFormatter(formatter)
logger.addHandler(sh)

fh = logging.FileHandler(log_file)
fh.setFormatter(formatter)
logger.addHandler(fh)

fh.setFormatter(formatter_process)

fh_human = logging.FileHandler(log_file_f("he_"))
fh_human.setFormatter(formatter_human)
logging.getLogger("he").addHandler(fh_human)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

mongo_uri = "mongodb://3030:sederfes100500@ds055525.mongolab.com:55525/reddit_people"
db_name = "reddit_people"

cfs_redis_address = "pub-redis-17140.us-east-1.1.azure.garantiadata.com"
cfs_redis_port = 17140
cfs_redis_password = "sederfes100500"

states_address = "https://read-shlak0bl0k.rhcloud.com/rockmongo/x"
states_user = "admin"
states_pwd = "YsrSQnuBJGhH"

osmdp = os.environ.get("OPENSHIFT_MONGODB_DB_PORT", "localhost")
osmdh = os.environ.get("OPENSHIFT_MONGODB_DB_HOST", "")
print "states data persist: ", osmdh, osmdp
states_conn_url = "mongodb://%s:%s@%s:%s/" % (states_user, states_pwd, osmdh, osmdp)
states_db_name = "read"

WORKED_PIDS_QUERY = os.environ.get("WORKED_PIDS_QUERY", "python2.7")

# logger.info(
#     "Reddit People MANAGEMENT SYSTEM STARTED... \nEnv:%s" % "\n".join(["%s:\t%s" % (k, v) for k, v in os.environ.iteritems()]))
