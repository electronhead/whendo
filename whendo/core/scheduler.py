from datetime import time
from pydantic import BaseModel, PrivateAttr
from typing import Dict, Optional
from collections.abc import Callable
import logging
from .util import Now, object_info
from .executor import Executor
from .timed import Timed

logger = logging.getLogger(__name__)


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

    start: Optional[time] = None
    stop: Optional[time] = None

    def schedule(self, scheduler_name: str, executor: Executor):
        pass

    def unschedule(self, scheduler_name: str):
        pass

    def during_period(self, scheduler_name: str, executor: Executor):
        """
        This method returns the thunk that ultimately gets invoked by the executor.

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

        if (self.start is not None) and (self.stop is not None):

            def is_in_period_wrapper(start: time, stop: time):
                def inner(now: time):
                    return (
                        (start < now and now < stop)
                        if (start < stop)
                        else (start < now or now < stop)
                    )

                return inner

            is_in_period = is_in_period_wrapper(start=self.start, stop=self.stop)

            def thunk():
                if is_in_period(Now.t()):
                    executor.push(scheduler_name)

            return thunk
        else:

            def thunk():
                executor.push(scheduler_name)

            return thunk

    def info(self):
        return object_info(self)

    def description(self):
        if (self.start is not None) and (self.stop is not None):
            return f"All between {self.start} and {self.stop}."
        else:
            return ""


class TimedScheduler(Scheduler):
    _timed: Timed = PrivateAttr()

    def get_timed(self):
        return self._timed

    def set_timed(self, timed: Timed):
        self._timed = timed

    def unschedule(self, scheduler_name: str):
        self._timed.clear(scheduler_name)


class ThresholdScheduler(Scheduler):
    pass


class Immediately(Scheduler):
    immediately: str = "immediately"

    def description(self):
        return (
            f"This scheduler executes its actions immediately. {super().description()}"
        )
