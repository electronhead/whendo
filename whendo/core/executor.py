"""
An Executor instance executes actions immediately based on scheduler names
supplied by time- or threshold-based schedulers. The actions associated with
the named scheduler are executed.
"""

from typing import Callable
import logging
from .exception import TerminateSchedulerException
from .action import log_action_result

logger = logging.getLogger(__name__)


class Executor:
    def __init__(
        self, get_actions_thunk: Callable, unschedule_scheduler_thunk: Callable
    ):
        self.get_actions_thunk = get_actions_thunk
        self.unschedule_scheduler_thunk = unschedule_scheduler_thunk

    def push(self, scheduler_name: str):
        """
        Time- or threshold-based event triggering calls this method.
        """
        actions_dictionary = self.get_actions_thunk(scheduler_name)
        for action_name in actions_dictionary:
            tag = f"{scheduler_name}:{action_name}"
            action = actions_dictionary[action_name]
            try:
                result = action.execute(tag=tag)
                log_action_result(
                    calling_logger=logger,
                    calling_object=self,
                    tag=f":{action_name}",
                    action=action,
                    result=result,
                )

            except TerminateSchedulerException as terminate:
                self.unschedule_scheduler_thunk(scheduler_name)
                logger.info(
                    f"Executor: tag ({tag}); unscheduled scheduler ({scheduler_name}); TerminateSchedulerException raised ({str(terminate)})"
                )
            except Exception as exception:
                logger.exception(
                    f"Executor: tag ({tag}); error while executing action ({action})",
                    exc_info=exception,
                )
