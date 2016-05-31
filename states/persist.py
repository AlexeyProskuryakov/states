import datetime
import logging

import pymongo

from states.properties import cfs_redis_address, states_db_name, states_conn_url, mongo_uri, db_name
from states import StateObject
from states.processes import ProcessDirector

log = logging.getLogger("state_persist")

HASH_STATES = "STATES"
STATE = lambda x: "state_%s" % (x)

STATE_TASK = "STATE_TASKS"

S_WORK, S_TERMINATED = "work", "terminated"

class DBHandler(object):
    def __init__(self, name="?", uri=mongo_uri, db_name=db_name):
        log.info("start db handler for [%s] %s" % (name, uri))
        self.mongo_client = pymongo.MongoClient(host=uri)
        self.db = self.mongo_client[db_name]


class StatePersist(ProcessDirector, DBHandler):
    def __init__(self, name="?", clear=False, max_connections=2):
        ProcessDirector.__init__(self, "state persist %s" % name, clear, max_connections)
        DBHandler.__init__(self, "state persist: %s" % name, uri=states_conn_url, db_name=states_db_name)

        log.info("State persist [ %s | %s ] inited for [%s]" % (cfs_redis_address, states_conn_url, name))
        try:
            self.state_data = self.db.create_collection("state_data", capped=True, max=1000)
            self.state_data.create_index("aspect")
            self.state_data.create_index([("time", pymongo.DESCENDING)], background=True)
        except Exception as e:
            self.state_data = self.db.get_collection("state_data")

    def set_state(self, aspect, state):
        return self.redis.hset(HASH_STATES, aspect, state)

    def get_state(self, aspect, history=False, worked_pids=None):
        global_state = self.redis.hget(HASH_STATES, aspect)
        pd_state = super(StatePersist, self).get_state(aspect, worked_pids=worked_pids)

        result = StateObject(global_state,
                             S_WORK if pd_state.get("work") else S_TERMINATED)
        if history:
            result.history = self.get_state_data(aspect)

        return result

    def set_state_data(self, aspect, data):
        self.state_data.insert_one(dict({"aspect": aspect, "time": datetime.datetime.utcnow()}, **data))

    def get_state_data(self, aspect):
        return list(self.state_data.find({"aspect": aspect}).sort("time", 1))

