from datetime import time
from pydantic import BaseModel
from typing import Optional
from collections.abc import Callable
from threading import RLock
import logging
from whendo.core.util import TimeUnit, Now, object_info
from whendo.core.action import Action
from whendo.core.continuous import Continuous
import random

logger = logging.getLogger(__name__)

class Count:
    """
    This counter is useful for distiguishing between different sets of log entries as well as viewing a count for each tag.
    """
    good_count = {}
    bad_count = {}
    @classmethod
    def good_up(cls, tag):
        if tag not in cls.good_count:
            cls.good_count[tag] = 0
        cls.good_count[tag] = 1 + cls.good_count[tag]
    @classmethod
    def bad_up(cls, tag):
        if tag not in cls.bad_count:
            cls.bad_count[tag] = 0
        cls.bad_count[tag] = 1 + cls.bad_count[tag]
    @classmethod
    def good(cls, tag):
        return cls.good_count.get(tag, 0)
    @classmethod
    def bad(cls, tag):
        return cls.bad_count.get(tag, 0)

class DoNothing:
    result = {"outcome":"DoNothing"}

class Scheduler(BaseModel):
    """
    An instance of the Scheduler class schedules Action instances using the Python 'schedule' library. This
    library schedules and runs 'jobs'. A submitted job can be any zero-arg Callable.
    
        https://schedule.readthedocs.io/en/stable/
    
    All Schedulers can limit the time during the day that their jobs run by setting the 'start' and 'stop'
    fields to instances of the 'datetime.datetime.time' class.
    
    examples:
        start=time(8,0,0) stop=time(18,0,0) limits execution to the time between 8:00 and 18:00
        start=time(18,0,0) stop=time(8,0,0) limits execution to the time between 18:00 and 8:00
    
    note:
        1. This (start, stop) in-period feature is implemented outside of the workings of the schedule library since schedule's schedule build 
           mechanism does not support it. So it's done using a less than optimal approach that alters the execution
           behavior within a scheduled job. Outside of the specified period, a job will be run. It just won't do anything. [see do_nothing below]
    """
    start: Optional[time]=None
    stop: Optional[time]=None
    
    def schedule_action(self, tag:str, action:Action, continuous:Continuous):
        pass
  
    def during_period(self, job_thunk:Callable[...,...], tag:str, action_info:object):
        """
        is_in_period_wrapper below takes (start) and (stop) and returns a 1-arg function that compares (start)
        and (stop) with a supplied time (now).

        if start<stop, then the active period is defined by
            start<now AND now<stop
            e.g. - 6:00 => 18:00
        if start>stop, then the period period is defined by
            start<now OR now<stop
            e.g. - 18:00 => 6:00
        
        This is done so that is_in_period is freshly evaluated at the times when the schedule library runs the job
        (that is meant to invoke the Callable).
        """
        scheduler_info = self.json()
        if (self.start is not None) and (self.stop is not None):
            is_in_period_wrapper = lambda start, stop: (lambda now: start < now and now < stop if (start < stop) else start < now or now < stop)
            is_in_period = is_in_period_wrapper(self.start, self.stop)
            do_nothing = lambda tag, scheduler_info: DoNothing.result
            return self.wrap(lambda: (job_thunk if is_in_period(Now.t()) else do_nothing)(tag=tag, scheduler_info=scheduler_info), tag=tag, action_info=action_info, scheduler_info=scheduler_info, do_nothing=False)
        else:
            return self.wrap(lambda: job_thunk(tag=tag, scheduler_info=scheduler_info), tag=tag, action_info=action_info, scheduler_info=scheduler_info, do_nothing=True)
    
    def wrap(self, thunk:Callable[...,...], tag:str, action_info:object, scheduler_info:object, do_nothing:bool):
        """
        wraps the execution inside a try block;
        allows for handling of logging and raised exceptions
        """
        result = None
        def execute():
            try:
                result = thunk()
                if result is DoNothing.result:
                    return result
                else:
                    Count.good_up(tag)
                    logger.info(f"({Count.good(tag):09}) tag={tag}")
                    logger.info(f"({Count.good(tag):09}) scheduler={scheduler_info}")
                    logger.info(f"({Count.good(tag):09}) action={action_info}")
            except Exception as exception:
                result = exception
                Count.bad_up(tag)
                logger.exception(f"({Count.bad(tag):09}) tag={tag}", exc_info=exception)
                logger.exception(f"({Count.bad(tag):09}) scheduler={scheduler_info}", exc_info=exception)
                logger.exception(f"({Count.bad(tag):09}) action={action_info}", exc_info=exception)
            return result
        return execute

    def info(self):
        return object_info(self)
    
class TimelyScheduler(Scheduler):
    """
    This scheduler executes Actions every [interval] days, hours, minutes, seconds at a
    time within the time unit (hour, minute, second).
    
    The time unit is determined by the values of the hour, minute, and second
    fields.

    If hour is specified, the time unit is set to day. [17:00:00]
    If minute is specified, the time unit is set to hour. [:15:00]
    If second is specified, the time unit is set to minute. [:15]
    Otherwise the time unit is set to second.

    For example, for hour=None, minute=15, second=None, interval=2, the system will
    execute the action every 2 hours at 15 minutes past the hour.
    """
    interval: int
    hour: Optional[int]=None
    minute: Optional[int]=None
    second: Optional[int]=None

    def schedule_action(self, tag:str, action:Action, continuous:Continuous):
        callable = self.during_period(action.execute, tag=tag, action_info=action.json())
        continuous.schedule_timely_callable(
            tag=tag,
            callable=callable,
            interval=self.interval,
            hour=self.hour, minute=self.minute, second=self.second)

class RandomlyScheduler(Scheduler):
    """
    This scheduler randomly executes Actions every [low] to [high] days, hours, minutes, or seconds.
    
    The time unit is supplied at instance creation.

    For example, for low=30, hight=90 and time_unit=second, the system will execute the action
    randomly every 30 to 90 seconds after each execution.
    """
    time_unit: Optional[TimeUnit]=TimeUnit.second
    low: int
    high: int

    def schedule_action(self, tag:str, action:Action, continuous:Continuous):
        callable = self.during_period(action.execute, tag=tag, action_info=action.json())
        continuous.schedule_random_callable(
            tag=tag,
            callable=callable,
            time_unit=self.time_unit,
            low=self.low, high=self.high)
