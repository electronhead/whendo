from typing import List, Dict, Any, Optional
from enum import Enum
import json
import logging
from whendo.core.action import Action


logger = logging.getLogger(__name__)


class Arg(Action):
    arg: str = "arg"
    data: dict

    def description(self):
        return f"This action returns ({self.data})."

    def execute(self, tag: str = None, data: dict = None):
        return self.data


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
            result = {
                "result": True,
                "exception": str(operand_result),
                "action": self.info(),
            }
            if data:
                result["data"] = data
            return result
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
    actions: List[Action]
    exception_on_no_success: bool = False

    def execute(self, tag: str = None, data: dict = None):
        (
            processing_count,
            success_count,
            failure_count,
            successful_actions,
            exception_actions,
            result,
        ) = process_actions(
            data=data,
            op_mode=self.op_mode,
            tag=tag,
            actions=self.actions,
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
            if isinstance(result, dict):
                if "result" in result:
                    result = result["result"]
            result = {
                "result": result,
                "outcome": "list action executed",
                "action": self.info(),
                "processing_info": processing_info,
            }
            if data:
                result["data"] = data
            return result


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


class IfElse(Action):
    """
    executes actions based on:

        if test_action is successful, executes if_action
        otherwise executes else_action

    """

    if_else: str = "if_else"
    test_action: Action
    else_action: Action
    if_action: Optional[Action]
    exception_on_no_success: bool = False

    def description(self):
        return f"If  action ({self.test_action}) succeeds, then IfElse executes ({self.if_action}), otherwise executes ({self.else_action})"

    def execute(self, tag: str = None, data: dict = None):
        try:
            test_result = self.test_action.execute(tag=tag, data=data)
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
            exception_dict = self.test_action.dict().copy()
            exception_dict.update({"exception": str(test_result)})
            exception_actions.append(exception_dict)

            try:
                else_result = self.else_action.execute(tag=tag, data=data)
            except Exception as exception:
                else_result = exception
            processing_count += 1
            if isinstance(else_result, Exception):
                exception_count += 1
                exception_dict = self.else_action.dict().copy()
                exception_dict.update({"exception": str(else_result)})
                exception_actions.append(exception_dict)
                result = exception_dict
            else:
                success_count += 1
                successful_actions.append(self.else_action.dict())
                result = else_result
        else:
            success_count += 1
            successful_actions.append(self.test_action.dict())

            if self.if_action:  # execute the if_action
                try:
                    if_result = self.if_action.execute(tag=tag, data=data)
                except Exception as exception:
                    if_result = exception
                processing_count += 1
                if isinstance(if_result, Exception):
                    exception_count += 1
                    exception_dict = self.if_action.dict().copy()
                    exception_dict.update({"exception": str(if_result)})
                    exception_actions.append(exception_dict)
                    result = exception_dict
                else:
                    success_count += 1
                    successful_actions.append(self.if_action.dict())
                    result = if_result
            else:  # just use test_result since there is no if_action
                result = test_result

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
            result = {
                "result": result,
                "outcome": "if else action executed",
                "tag": tag,
                "action": self.info(),
                "processing_info": processing_info,
            }
            if data:
                result["data"] = data
            return result


def process_actions(
    op_mode: ListOpMode,
    actions: List[Action],
    tag: str = None,
    data: dict = None,
    successful_actions: List[Dict[Any, Any]] = [],
    exception_actions: List[Dict[Any, Any]] = [],
    processing_count: int = 0,
    success_count: int = 0,
    exception_count: int = 0,
):
    """
    services the two action list classes
    """
    loop_data = data
    for action in actions:
        try:  # in case an Action does not return an exception
            result = action.execute(tag=tag, data=loop_data)
        except Exception as exception:
            result = exception
        processing_count += 1
        if isinstance(result, Exception):
            exception_count += 1
            exception_dict = action.dict().copy()
            exception_dict.update({"exception": str(result)})
            exception_actions.append(exception_dict)
            if op_mode == ListOpMode.AND:  # stop after first failure
                break
            loop_data = exception_dict
        else:
            success_count += 1
            successful_actions.append(action.dict())
            loop_data = result if isinstance(result, dict) else {"result": result}
            if op_mode == ListOpMode.OR:  # stop after first success
                break
    return (
        processing_count,
        success_count,
        exception_count,
        successful_actions,
        exception_actions,
        loop_data,
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
        for action in self.actions:
            data = action.execute(tag=tag, data=data)
        return data
