from typing import List, Dict, Any, Optional
from enum import Enum
import json
import logging
from collections import namedtuple
from whendo.core.action import Action
from whendo.core.exception import TerminateSchedulerException


logger = logging.getLogger(__name__)


def processing_results(
    result: Any,
    processing_count: int = 0,
    success_count: int = 0,
    exception_count: int = 0,
    successful_actions: List[Dict[Any, Any]] = [],
    exception_actions: List[Dict[Any, Any]] = [],
):
    return {
        "result": result,
        "processing_count": processing_count,
        "success_count": success_count,
        "exception_count": exception_count,
        "successful_actions": successful_actions,
        "exception_actions": exception_actions,
    }


class Arg(Action):
    arg: str = "arg"
    data: dict

    def description(self):
        return f"This action returns ({self.data})."

    def execute(self, tag: str = None, data: dict = None):
        return self.data


class Terminate(Action):
    terminate: str = "terminate"

    def description(self):
        return f"This action raises a TerminateScheduler exception."

    def execute(self, tag: str = None, data: dict = None):
        raise TerminateSchedulerException(value=tag)


class Failure(Action):
    """ acts like False """

    failure: str = "failure"

    def description(self):
        return f"This action always fails. It serves a role similar to the bool, False."

    def execute(self, tag: str = None, data: dict = None):
        raise Exception("purposely unsuccessful execution", self.json())


class Success(Action):
    """ acts like True. It also serves as a fixed point execute implementation. """

    success: str = "success"

    def description(self):
        return (
            f"This action always succeeds. It serves a role similar to the bool, True."
        )

    def execute(self, tag: str = None, data: dict = None):
        return data


class Not(Action):
    """ acts like negation """

    _not: str = "not"
    operand: Action

    def description(self):
        return f"If the operand ({self.operand}) fails, Not succeeds, otherwise fails (throwing an Exception). It serves a role similar to logical negation."

    def execute(self, tag: str = None, data: dict = None):
        operand_result = None
        try:
            operand_result = self.operand.execute(tag=tag, data=data)
        except Exception as exception:
            operand_result = exception
        if isinstance(operand_result, Exception):
            extra = {
                "exception": str(operand_result),
                "action": self.info(),
            }
            return self.action_result(result=True, data=data, extra=extra)
        else:
            raise Exception(
                "exception generated; action execution treated as a failure",
                self.json(),
            )


class ListOpMode(str, Enum):
    ALL = "all"
    OR = "or"
    AND = "and"


class ListAction(Action):
    """
    executes actions based on:

        ListOpMode.ALL:   executes all, irrespective of individual outcomes
        ListOpMode.OR:    executes until the first successful action (no exception)
        ListOpMode.AND:   executes until the first exception (failure)

    Intended to be abstract class; not intended to be instantiated. Its subclasses,
    All, Or, and And, should be used instead.
    """

    op_mode: ListOpMode
    actions: List[Action] = []
    exception_on_no_success: bool = False
    result_only: bool = True

    def execute(self, tag: str = None, data: dict = None):
        processing_info = process_actions(
            data=data,
            op_mode=self.op_mode,
            tag=tag,
            actions=self.actions,
            successful_actions=[],
            exception_actions=[],
        )
        if (
            processing_info["processing_count"] > 0
            and processing_info["success_count"] == 0
            and self.exception_on_no_success
        ):
            raise Exception(
                "exception generated; all actions failiing treated as a list action failure",
                json.dumps(self.dict()),
                json.dumps(processing_info),
            )
        return processing_info["result"] if self.result_only else processing_info


class All(ListAction):
    """
    executes all actions
    """

    _all: str = "all"
    op_mode: ListOpMode = ListOpMode.ALL

    def description(self):
        return f"This action executes all of these actions in order: ({self.actions})."

    def execute(self, tag: str = None, data: dict = None):
        return super().execute(tag=tag, data=data)


class Or(ListAction):
    """
    executes actions until first success
    """

    _or: str = "or"
    op_mode: ListOpMode = ListOpMode.OR

    def description(self):
        return f"This action executes all of these actions in order until the first success: ({self.actions}). It serves a role similar to logical or."

    def execute(self, tag: str = None, data: dict = None):
        return super().execute(tag=tag, data=data)


class And(ListAction):
    """
    executes actions until first failure
    """

    _and: str = "and"
    op_mode: ListOpMode = ListOpMode.AND

    def description(self):
        return f"This action executes all of these actions in order until the first failure: ({self.actions}). It serves a role similar to logical and."

    def execute(self, tag: str = None, data: dict = None):
        return super().execute(tag=tag, data=data)


def process_actions(
    op_mode: ListOpMode,
    actions: List[Action],
    tag: str = None,
    data: Dict[Any, Any] = None,
    successful_actions: List[Dict[Any, Any]] = [],
    exception_actions: List[Dict[Any, Any]] = [],
    processing_count: int = 0,
    success_count: int = 0,
    exception_count: int = 0,
):
    """
    services the three action list classes, ALL, OR, and AND
    """
    exceptions: List[Exception] = []
    loop_data = data
    for action in actions:
        try:
            result = action.execute(tag=tag, data=loop_data)
            logger.info(
                f"Execution: tag ({tag}); executed action ({action}); loop data ({loop_data})"
            )
        except Exception as exception:
            result = exception
            logger.exception(
                f"Execution: tag ({tag}); error while executing action ({action}); loop data ({loop_data})",
                exc_info=exception,
            )
        processing_count += 1
        if isinstance(result, Exception):
            exception_count += 1
            exception_dict = action.dict().copy()
            exception_dict.update({"exception": str(result)})
            exception_actions.append(exception_dict)
            if isinstance(result, TerminateSchedulerException):
                result.value = processing_results(
                    loop_data,
                    processing_count,
                    success_count,
                    exception_count,
                    successful_actions,
                    exception_actions,
                )
                raise result
            if op_mode == ListOpMode.AND:  # stop after first failure
                break
            loop_data = exception_dict
        else:
            success_count += 1
            successful_actions.append(action.dict())
            loop_data = result
            if op_mode == ListOpMode.OR:  # stop after first success
                break
    return processing_results(
        loop_data,
        processing_count,
        success_count,
        exception_count,
        successful_actions,
        exception_actions,
    )


# experimental


class Compose(Action):
    compose: str = "compose"
    actions: List[Action]

    def description(self):
        return (
            f"Performs function composition on supplied actions in left-to-right order."
        )

    def execute(self, tag: str = None, data: dict = None):
        loop_data = data
        for action in self.actions:
            loop_data = action.execute(tag=tag, data=loop_data)
        return loop_data
