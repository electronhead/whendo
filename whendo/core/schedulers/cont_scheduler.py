from typing import Optional
import logging
import random
from whendo.core.util import TimeUnit
from whendo.core.action import Action
from whendo.core.scheduler import Scheduler
from whendo.core.continuous import Continuous

logger = logging.getLogger(__name__)


class Timely(Scheduler):
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

    def schedule_action(self, tag: str, action: Action, continuous: Continuous):
        callable = self.during_period(tag=tag, action=action)
        continuous.schedule_timely_callable(
            tag=tag,
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


class Randomly(Scheduler):
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

    def schedule_action(self, tag: str, action: Action, continuous: Continuous):
        callable = self.during_period(tag=tag, action=action)
        continuous.schedule_random_callable(
            tag=tag,
            callable=callable,
            time_unit=self.time_unit,
            low=self.low,
            high=self.high,
        )


class Immediately(Scheduler):
    immediately: str = "immediately"

    def description(self):
        return (
            f"This scheduler executes its actions immediately. {super().description()}"
        )

    def schedule_action(self, tag: str, action: Action, continuous: Continuous):
        """
        Wrapping ensures that the execution of the action participates in logging
        in the same manner as actions that are executed in the Continuous job
        system.
        """
        wrapped_callable = self.wrap(
            thunk=lambda: action.execute(tag=tag, scheduler_info=self.info()),
            tag=tag,
            action_json=action.json(),
            scheduler_json=self.json(),
        )
        wrapped_callable()

    def joins_schedulers_actions(self):
        return False
