from typing import Optional
import logging
from whendo.core.util import TimeUnit
from whendo.core.scheduler import TimedScheduler
from whendo.core.timed import Timed
from whendo.core.executor import Executor

logger = logging.getLogger(__name__)


class Timely(TimedScheduler):
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
    hour: Optional[int] = None
    minute: Optional[int] = None
    second: Optional[int] = None

    def description(self):
        return f"This scheduler executes its actions every {self.time_as_str()}. {super().description()}"

    def schedule(self, scheduler_name: str, executor: Executor):
        self.unschedule(scheduler_name)
        callable = self.during_period(scheduler_name=scheduler_name, executor=executor)
        self.get_timed().schedule_timely_callable(
            tag=scheduler_name,
            callable=callable,
            interval=self.interval,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
        )

    def time_as_str(self):
        hour = self.hour
        minute = self.minute
        second = self.second
        interval = self.interval
        if hour:
            if minute is None:
                minute = 0
            if second is None:
                second = 0
            return f"{interval} day{'s' if interval > 1 else ''} at {hour:02}:{minute:02}:{second:02}."
        elif minute:
            if second is None:
                second = 0
            return f"{interval} hours{'s' if interval > 1 else ''} at :{minute:02}:{second:02} past the hour."
        elif second:
            return f"{interval} minute{'s' if interval > 1 else ''} at :{second:02} past the minute."
        else:
            return f"{interval} second{'s' if interval > 1 else ''}"


class Randomly(TimedScheduler):
    """
    This scheduler randomly executes Actions every [low] to [high] days, hours, minutes, or seconds.

    The time unit is supplied at instance creation.

    For example, for low=30, hight=90 and time_unit=second, the system will again execute the action
    randomly every 30 to 90 seconds after each execution.
    """

    time_unit: TimeUnit = TimeUnit.second
    low: int
    high: int

    def description(self):
        return f"This scheduler executes its actions every {self.low} to {self.high} {self.time_unit.value}s. {super().description()}"

    def schedule(self, scheduler_name: str, executor: Executor):
        self.unschedule(scheduler_name)
        callable = self.during_period(scheduler_name=scheduler_name, executor=executor)
        self.get_timed().schedule_random_callable(
            tag=scheduler_name,
            callable=callable,
            time_unit=self.time_unit,
            low=self.low,
            high=self.high,
        )
