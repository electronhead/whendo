"""
This module contains the class that schedules and runs jobs.
"""

from schedule import Scheduler
from threading import Event, Thread
import time
from collections.abc import Callable
import logging
from whendo.core.util import Now, TimeUnit

logger = logging.getLogger(__name__)

class Continuous(Scheduler):
    """
    This class extends the functionality of schedule.Scheduler using code from github [see below]
    that runs jobs continuously in a separate thread. There is no need to invoke run_pending()
    in a loop.

    docs:
        https://schedule.readthedocs.io/en/stable/

    usage of additional methods:
        continuous = Continuous()
        continuous.job_count()
        continuous.is_running()
        continuous.run_continuously()
        continuous.stop_running_continuously()
    """
    instance = None
    @classmethod
    def get(cls):
        if not cls.instance:
            cls.instance = Continuous()
        return cls.instance

    def __init__(self):
        super().__init__()
        self.cease_continuous_run = None
  
    def is_running(self):
        if not self.cease_continuous_run:
            return False
        if self.cease_continuous_run.is_set():
            return False
        else:
            return True
    
    def job_count(self):
        return len(self.jobs)
  
    def stop_running_continuously(self):
        if self.cease_continuous_run:
            if self.cease_continuous_run.is_set():
                logger.info(f"continuous run already stopped")
            else:
                self.cease_continuous_run.set()
                logger.info(f"continuous run stopped")
        else:
            logger.info(f"yet to run continuously")

    #
    # from https://github.com/mrhwick/schedule/blob/master/schedule/__init__.py
    # ... ensures one active invocation of run_continuously at a
    #
    def run_continuously(self, interval=1):
        """
        Continuously run, while executing pending jobs at each elapsed
        time interval.
        @return cease_continuous_run: threading.Event which can be set to
        cease continuous run.
        Please note that it is *intended behavior that run_continuously()
        does not run missed jobs*. For example, if you've registered a job
        that should run every minute and you set a continuous run interval
        of one hour then your job won't be run 60 times at each interval but
        only once.
        """
        # do not run again if already running. Stop first, then run again.
        assert True if self.cease_continuous_run == None else self.cease_continuous_run.is_set()

        self.cease_continuous_run = Event()

        class ScheduleThread(Thread):
            @classmethod
            def run(cls):
                while not self.cease_continuous_run.is_set():
                    self.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.setDaemon(True)
        continuous_thread.start()
        logger.info(f"started running continuously")

    # methods added to adapt to Dispatcher scheduling model (an adaptation of the schedule library model)
    def schedule_timely_callable(self, tag:str, callable:Callable, interval:int=1, hour:int=None, minute:int=None, second:int=None):
        time_unit, clock_time = TimeUnit.second, None # on a second boundary
        if hour is not None:
            if minute is None:
                minute = 0
            if second is None:
                second = 0
            time_unit, clock_time = TimeUnit.day, f"{hour:02}:{minute:02}:{second:02}" # 16:15:05 on a day boundary
        elif minute is not None:
            if second is None:
                second = 0
            time_unit, clock_time = TimeUnit.hour, f":{minute:02}:{second:02}" # :15:05 on an hour boundary
        elif second is not None:
            time_unit, clock_time =  TimeUnit.minute, f":{second:02}" # :05 on a minute boundary

        if time_unit == TimeUnit.day:
            self.every(interval).day.at(clock_time).do(callable).tag(tag)
        elif time_unit == TimeUnit.hour:
            self.every(interval).hour.at(clock_time).do(callable).tag(tag)
        elif time_unit == TimeUnit.minute:
            self.every(interval).minute.at(clock_time).do(callable).tag(tag)
        elif time_unit == TimeUnit.second:
            self.every(interval).second.do(callable).tag(tag)

    def schedule_random_callable(self, tag:str, callable:Callable, time_unit:TimeUnit, low:int, high:int):
        if time_unit == TimeUnit.second:
            self.every(low).to(high).seconds.do(callable).tag(tag)
        elif time_unit == TimeUnit.minute:
            self.every(low).to(high).minutes.do(callable).tag(tag)
        elif time_unit == TimeUnit.hour:
            self.every(low).to(high).hours.do(callable).tag(tag)
        elif time_unit == TimeUnit.day:
            self.every(low).to(high).days.do(callable).tag(tag)