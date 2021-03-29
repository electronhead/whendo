"""
An Executor instance executes actions immediately based on scheduler names
supplied by time- or threshold-based schedulers. The actions associated with
the named scheduler are executed.
"""

from typing import Callable
import logging

logger = logging.getLogger(__name__)


class Executor:
    def __init__(self, get_actions_thunk: Callable):
        self.get_actions_thunk = get_actions_thunk

    def push(self, scheduler_name: str):
        """
        The event triggering mechanism (time- or threshold-based) calls this method.
        """
        actions_dictionary = self.get_actions_thunk(scheduler_name)
        for action_name in actions_dictionary:
            try:
                actions_dictionary[action_name].execute(
                    tag=f"{scheduler_name}:{action_name}"
                )
            except Exception as e:
                logging.error(f"Executor execution error: ({str(e)}")
