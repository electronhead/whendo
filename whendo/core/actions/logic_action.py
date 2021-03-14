from typing import List, Dict, Any, Optional
from enum import Enum
import json
import logging
from whendo.core.action import Action


logger = logging.getLogger(__name__)


class Failure(Action):
    """ acts like False """

    logic_failure: str = "failure"

    def description(self):
        return f"This action always fails. It serves a role similar to the bool, False."

    def execute(self, tag: str = None, scheduler_info: dict = None):
        raise Exception("purposely unsuccessful execution", self.json())


class Success(Action):
    """ acts like True """

    logic_success: str = "success"

    def description(self):
        return (
            f"This action always succeeds. It serves a role similar to the bool, True."
        )

    def execute(self, tag: str = None, scheduler_info: dict = None):
        return {"outcome": "purposely successful execution", "action": self.info()}


class Not(Action):
    """ acts like negation """

    logic_not: str = "not"
    operand: Action

    def description(self):
        return f"If the operand ({self.operand}) fails, Not succeeds, otherwise fails (throwing an Exception). It serves a role similar to logical negation."

    def execute(self, tag: str = None, scheduler_info: dict = None):
        operand_result = None
        try:
            operand_result = self.operand.execute(
                tag=tag, scheduler_info=scheduler_info
            )
        except Exception as exception:
            operand_result = exception
        if isinstance(operand_result, Exception):
            return {
                "outcome": "exception negated; action execution treated as a success",
                "exception": str(operand_result),
                "action": self.info(),
            }
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
    action_list: List[Action]
    exception_on_no_success: bool = False

    def execute(self, tag: str = None, scheduler_info: Dict[str, Any] = None):
        (
            processing_count,
            success_count,
            failure_count,
            successful_actions,
            exception_actions,
        ) = process_action_list(
            tag,
            scheduler_info,
            self.op_mode,
            action_list=self.action_list,
            successful_actions=[],
            exception_actions=[],
        )
        processing_info = {
            "processing_count": processing_count,
            "success_count": success_count,
            "exception_count": failure_count,
            "successful_actions": successful_actions,
            "exception_actions": exception_actions,
        }
        if success_count == 0 and self.exception_on_no_success:
            raise Exception(
                "exception generated; action execution treated as a failure",
                json.dumps(self.dict()),
                json.dumps(processing_info),
            )
        else:
            return {
                "outcome": "list action executed",
                "action": self.info(),
                "processing_info": processing_info,
            }


class All(ListAction):
    """
    executes all actions
    """

    logic_all: str = "all"
    op_mode: ListOpMode = ListOpMode.ALL

    def description(self):
        return (
            f"This action executes all of these actions in order: ({self.action_list})."
        )

    def execute(self, tag: str = None, scheduler_info: Dict[str, Any] = None):
        return super().execute(tag=tag, scheduler_info=scheduler_info)


class Or(ListAction):
    """
    executes actions until first success
    """

    logic_or: str = "or"
    op_mode: ListOpMode = ListOpMode.OR

    def description(self):
        return f"This action executes all of these actions in order until the first success: ({self.action_list}). It serves a role similar to logical or."

    def execute(self, tag: str = None, scheduler_info: Dict[str, Any] = None):
        return super().execute(tag=tag, scheduler_info=scheduler_info)


class And(ListAction):
    """
    executes actions until first failure
    """

    logic_and: str = "and"
    op_mode: ListOpMode = ListOpMode.AND

    def description(self):
        return f"This action executes all of these actions in order until the first failure: ({self.action_list}). It serves a role similar to logical and."

    def execute(self, tag: str = None, scheduler_info: Dict[str, Any] = None):
        return super().execute(tag=tag, scheduler_info=scheduler_info)


class IfElse(Action):
    """
    executes actions based on:

        if test_action is successful, executes if_action
        otherwise executes else_action

    """

    logic_if_else: str = "if_else"
    test_action: Action
    if_action: Action
    else_action: Action
    exception_on_no_success: bool = False

    def description(self):
        return f"If  action ({self.test_action}) succeeds, then IfElse executes ({self.if_action}), otherwise executes ({self.else_action})"

    def execute(self, tag: str = None, scheduler_info: dict = None):
        try:
            test_result = self.test_action.execute(
                tag=tag, scheduler_info=scheduler_info
            )
        except Exception as exception:
            test_result = exception
        processing_count = 1
        success_count = 0
        exception_count = 0
        successful_actions = []
        exception_actions = []
        else_test = isinstance(test_result, Exception)
        if else_test:  # execute the else action
            exception_count = 1
            exception_actions.append(self.test_action.dict())

            try:
                else_result = self.else_action.execute(
                    tag=tag, scheduler_info=scheduler_info
                )
            except Exception as exception:
                else_result = exception
            processing_count += 1
            if isinstance(else_result, Exception):
                exception_count += 1
                exception_actions.append(self.else_action.dict())
            else:
                success_count += 1
                successful_actions.append(self.else_action.dict())
        else:
            success_count += 1
            successful_actions.append(self.test_action.dict())

            try:
                if_result = self.if_action.execute(
                    tag=tag, scheduler_info=scheduler_info
                )
            except Exception as exception:
                if_result = exception
            processing_count += 1
            if isinstance(if_result, Exception):
                exception_count += 1
                exception_actions.append(self.if_action.dict())
            else:
                success_count += 1
                successful_actions.append(self.if_action.dict())

        processing_info = {
            "else_test": else_test,
            "processing_count": processing_count,
            "success_count": success_count,
            "exception_count": exception_count,
            "successful_actions": successful_actions,
            "exception_actions": exception_actions,
        }
        if success_count == 0 and self.exception_on_no_success:
            raise Exception(
                "exception generated; action execution treated as a failure",
                json.dumps(self.dict()),
                json.dumps(processing_info),
            )
        else:
            return {
                "outcome": "if else action executed",
                "action": self.info(),
                "processing_info": processing_info,
            }


def process_action_list(
    tag: Optional[str],
    scheduler_info: Optional[Dict[str, Any]],
    op_mode: ListOpMode,
    action_list: List[Action],
    processing_count: int = 0,
    success_count: int = 0,
    exception_count: int = 0,
    successful_actions: List[Dict[Any, Any]] = [],
    exception_actions: List[Dict[Any, Any]] = [],
):
    """
    services the two action list classes
    """
    for action in action_list:
        try:  # in case an Action does not return an exception
            result = action.execute(tag=tag, scheduler_info=scheduler_info)
        except Exception as exception:
            result = exception
        processing_count += 1
        if isinstance(result, Exception):
            exception_count += 1
            exception_actions.append(action.dict())
            if op_mode == ListOpMode.AND:  # stop after first failure
                break
        else:
            success_count += 1
            successful_actions.append(action.dict())
            if op_mode == ListOpMode.OR:  # stop after first success
                break
    return (
        processing_count,
        success_count,
        exception_count,
        successful_actions,
        exception_actions,
    )
