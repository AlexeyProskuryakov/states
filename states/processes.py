# coding:utf-8
import logging
from multiprocessing.synchronize import Lock

import redis

from states.properties import cfs_redis_address, cfs_redis_port, cfs_redis_password
from states import get_worked_pids

log = logging.getLogger("process_director")

PREFIX = lambda x: "PD_%s" % x
PREFIX_QUERY = "PD_*"
PREFIX_GET_DATA = lambda x: x.replace("PD_", "") if isinstance(x, (str, unicode)) and x.count("PD_") == 1 else x


class ProcessDirector(object):
    def __init__(self, name="?", clear=False, max_connections=2):
        self.redis = redis.StrictRedis(host=cfs_redis_address,
                                       port=cfs_redis_port,
                                       password=cfs_redis_password,
                                       db=0,
                                       max_connections=max_connections
                                       )
        if clear:
            self.redis.flushdb()

        self.mutex = Lock()
        log.info("Inited")

    def start_aspect(self, aspect, pid):
        """
        starting or returning False if aspect already started
        :param aspect:
        :param pid:
        :return:
        """
        with self.mutex:
            log.info("will start aspect %s for %s" % (aspect, pid))
            result = self.redis.setnx(PREFIX(aspect), pid)
            if not result:
                aspect_pid = int(self.redis.get(PREFIX(aspect)))
                log.info("setnx result is None... aspect pid is: %s" % aspect_pid)
                if aspect_pid in get_worked_pids():
                    return {"state": "already work", "by": aspect_pid, "started": False}
                else:
                    p = self.redis.pipeline()
                    p.delete(PREFIX(aspect))
                    p.set(PREFIX(aspect), pid)
                    p.execute()
                    return {"state": "restarted", "started": True}
            else:
                return {"state": "started", "started": True}

    def stop_aspect(self, aspect):
        return self.redis.delete(PREFIX(aspect))

    def get_states(self):
        keys = self.redis.keys(PREFIX_QUERY)
        if keys:
            result = []
            worked_pids = get_worked_pids()
            for key in keys:
                pid = int(self.redis.get(key))
                result.append({"aspect": PREFIX_GET_DATA(key), "pid": pid, "work_at_cur_machine": pid in worked_pids})
            return result

    def get_state(self, aspect, worked_pids=None):
        pid_raw = self.redis.get(PREFIX(aspect))
        result = {"aspect": aspect,}
        wp = worked_pids or get_worked_pids()
        if pid_raw:
            pid = int(pid_raw)
            result = dict(result, **{"pid": pid, "work": pid in wp})
        else:
            result["work"] = False
        return result


if __name__ == '__main__':
    pd = ProcessDirector()

    from multiprocessing import current_process

    cur_pid = current_process().pid
    print "cur pid: ", cur_pid

    result1 = pd.start_aspect("test", cur_pid)
    print "result 1: ", result1
    result2 = pd.start_aspect("test", cur_pid)
    print "result 2: ", result2

    print "get state: ", pd.get_state("test")
    print "get states: ", pd.get_states()

    print  "stop aspect: ", pd.stop_aspect("test")
    print "---------------------------"

    result1 = pd.start_aspect("test1", cur_pid)
    print "before for test 1): ", result1
    result2 = pd.start_aspect("test2", cur_pid)
    print "before for test 2): ", result2

    print "get state: ", pd.get_state("test")
    print "get states: ", pd.get_states()

    print "after test1 1234", pd.start_aspect("test1", 1234)
    print "after test1 cur", pd.start_aspect("test1", cur_pid)
    print "after test1 1234", pd.start_aspect("test1", 1234)
    print "get state: ", pd.get_state("test1")

    print "after test2 1234", pd.start_aspect("test2", 1234)
    print "after test2 cur", pd.start_aspect("test2", cur_pid)
    print "after test2 1234", pd.start_aspect("test2", 1234)
    print "get state: ", pd.get_state("test2")

    print "get states: ", pd.get_states()

    print "stop: ", pd.stop_aspect("test1")
    print "stop: ", pd.stop_aspect("test2")

    print "get states: ", pd.get_states()
