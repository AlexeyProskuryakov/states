# coding:utf-8
import logging

import redis
import time
from threading import Thread, Event

from states import ConfigManager

log = logging.getLogger("process_director")

PREFIX_ALLOC = lambda x: "PD_%s" % x

DEFAULT_TICK_TIME = 10


class _ProcessTracker(object):
    def __init__(self, aspect, pd, tick_time):
        event = Event()
        self.tsh = Thread(target=_send_heart_beat, args=(aspect, pd, tick_time, event))
        self.tsh.setDaemon(True)
        self.tsh.start()

        self.stop_event = event

    def stop_track(self):
        log.info("will stop tracking")
        self.stop_event.set()
        self.tsh.join()


def _send_heart_beat(aspect, pd, tick_time, stop_event):
    log.info("start tracking [%s] every [%s]" % (aspect, tick_time))

    while not stop_event.isSet():
        try:
            pd._set_timed_state(aspect, tick_time)
        except Exception as e:
            log.exception(e)
        time.sleep(tick_time)

    log.info("stop tracking [%s]" % aspect)


class ProcessDirector(object):
    def __init__(self, name="?", clear=False, max_connections=2):
        cm = ConfigManager()
        self.redis = redis.StrictRedis(host=cm.get('process_director_redis_address'),
                                       port=cm.get('process_director_redis_port'),
                                       password=cm.get('process_director_redis_password'),
                                       db=0,
                                       max_connections=max_connections
                                       )
        if clear:
            self.redis.flushdb()

        log.info("Process director [%s] inited." % name)

    def start_aspect(self, aspect, tick_time=DEFAULT_TICK_TIME):
        alloc = self.redis.set(PREFIX_ALLOC(aspect), tick_time, ex=tick_time, nx=True)

        if alloc:
            result = _ProcessTracker(aspect, self, tick_time)
            return result

    def is_aspect_work(self, aspect):
        tick_time = self.redis.get(PREFIX_ALLOC(aspect))
        if tick_time:
            time.sleep(int(tick_time))
            tick_time = self.redis.get(PREFIX_ALLOC(aspect))

        return tick_time is not None

    def _set_timed_state(self, aspect, ex):
        self.redis.set(PREFIX_ALLOC(aspect), ex, ex=ex)
