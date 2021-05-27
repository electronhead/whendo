from typing import List, Dict, Any, Optional
from enum import Enum
import json
import logging
from collections import namedtuple
from whendo.core.action import Action, Rez, log_action_result
from whendo.core.exception import TerminateSchedulerException


logger = logging.getLogger(__name__)


def processing_results(
    rez: Rez = None,
    processing_count: int = 0,
    success_count: int = 0,
    exception_count: int = 0,
    successful_actions: List[Dict[Any, Any]] = [],
    exception_actions: List[Dict[Any, Any]] = [],
):
    return {
        "result": rez,
        "processing_count": processing_count,
        "success_count": success_count,
        "exception_count": exception_count,
        "successful_actions": successful_actions,
        "exception_actions": exception_actions,
    }


class Vals(Action):
    """
    flds in this object override supplied rez.flds.
    """

    _vals: str = "_vals"
    vals: Optional[dict] = None

    def description(self):
        return f"This action adds ({self.vals}) to the field value flow."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        rez_flds = rez.flds.copy() if rez and rez.flds else {}
        rez_flds.update(flds.get("vals", {}))
        return self.action_result(
            result=rez.result if rez else None, rez=rez, flds=rez_flds
        )


class Result(Action):
    result: str = "result"
    value: Any

    def description(self):
        return f"This action returns the stored value as a Rez.result."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        value = flds["value"]
        return self.action_result(result=value, rez=rez, flds=rez.flds if rez else {})


class RaiseCmp(Action):
    """
    The execute method of this action will raise an exception if:

    1. both RaiseCmp.value, Rez.result are not None
    AND
    2. if RaiseCmp.cmp < 0 AND Rez.Result < RaiseCmp.value
       OR if RaiseCmp.cmp == 0 AND Rez.Result == RaiseCmp.value
       OR if RaiseCmp.cmp > 0 AND Rez.Result > RaiseCmp.value

    """

    raise_cmp: str = "raise_cmp"
    value: Optional[Any] = None
    cmp: Optional[int] = None

    def description(self):
        return f"This action raises an exception if the supplied result {self.operand_str()} the action's value"

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        result = rez.result if rez else None
        value = flds.get("value", None)
        if result is None or value is None:
            should_raise = False
            logger.info(
                f"one of RaiseCmp.value, Rez.result equals None; RaiseCmp ignored; info ({self.info()}"
            )
        else:
            cmp = flds.get("cmp", 0)
            should_raise = (
                result < value
                if cmp < 0
                else (result == value if cmp == 0 else result > value)
            )
        if should_raise:
            raise ValueError(
                f"exception thrown because ({value}) ({self.operand_str(flds['cmp'])}) ({result}); info ({self.info()})"
            )
        else:
            return self.action_result(
                result=result,
                rez=rez,
                flds=rez.flds if rez else {},
            )

    def operand_str(self, cmp: Optional[int] = None):
        if cmp is None:
            cmp = (
                self.cmp if self.cmp is not None else 0
            )  # compiler doesn't catch that self.cmp is not None
        return "<" if cmp < 0 else ("=" if cmp == 0 else ">")


class Terminate(Action):
    terminate: str = "terminate"

    def description(self):
        return f"This action raises a TerminateScheduler exception."

    def execute(self, tag: str = None, rez: Rez = None):
        raise TerminateSchedulerException(value=tag)


class Failure(Action):
    """ acts like False """

    failure: str = "failure"

    def description(self):
        return f"This action always fails. It serves a role similar to the bool, False."

    def execute(self, tag: str = None, rez: Rez = None):
        raise Exception("purposely unsuccessful execution", self.json())


class Success(Action):
    """ acts like True. It also serves as a fixed point execute implementation. """

    success: str = "success"

    def description(self):
        return (
            f"This action always succeeds. It serves a role similar to the bool, True."
        )

    def execute(self, tag: str = None, rez: Rez = None):
        return rez


class Fail(Action):
    """ acts like negation """

    fail: str = "fail"
    operand: Action

    def description(self):
        return f"If the operand ({self.operand}) fails, Not succeeds, otherwise fails (throwing an Exception). It serves a role similar to logical negation."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        operand = flds["operand"]
        operand_result = None
        try:
            operand_result = operand.execute(tag=tag, rez=rez)
            log_action_result(
                calling_logger=logger,
                calling_object=self,
                tag=tag,
                action=operand,
                result=operand_result,
            )
        except Exception as exception:
            operand_result = exception
        if isinstance(operand_result, Exception):
            extra = {"execption": str(operand_result)}
            return self.action_result(
                result=True, rez=rez, flds=rez.flds if rez else {}, extra=extra
            )
        else:
            raise Exception(
                "exception generated; action execution treated as a failure",
                self.json(),
            )


class ListOpMode(str, Enum):
    ALL = "all"
    UNTIL_SUCCESS = "until_success"
    UNTIL_FAILURE = "until_failure"


class ListAction(Action):
    """
    executes actions based on:

        ListOpMode.ALL:   executes all, irrespective of individual outcomes
        ListOpMode.UNTIL_SUCCESS:    executes until the first successful action (no exception)
        ListOpMode.UNTIL_FAILURE:   executes until the first exception (failure)

    Intended to be abstract class; not intended to be instantiated. Its subclasses,
    All, Or, and And, should be used instead.
    """

    actions: List[Action] = []
    op_mode: Optional[ListOpMode] = None
    exception_on_no_success: Optional[bool] = None
    include_processing_info: Optional[bool] = None

    def description(self):
        if self.op_mode == ListOpMode.ALL:
            return (
                f"This action executes all of these actions in order: ({self.actions})."
            )
        if self.op_mode == ListOpMode.UNTIL_SUCCESS:
            return f"This action executes all of these actions in order until the first success: ({self.actions}). It serves a role similar to logical or."
        if self.op_mode == ListOpMode.UNTIL_FAILURE:
            return f"This action executes all of these actions in order until the first failure: ({self.actions}). It serves a role similar to logical and."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        processing_info = process_actions(
            calling_object=self,
            rez=rez,
            op_mode=flds.get("op_mode", ListOpMode.ALL),
            tag=tag,
            actions=flds["actions"],
            successful_actions=[],
            exception_actions=[],
        )
        if (
            processing_info["processing_count"] > 0
            and processing_info["success_count"] == 0
            and flds.get("exception_on_no_success", False)
        ):
            raise Exception(
                "exception generated; all actions failing treated as a list action failure",
                json.dumps(self.dict()),
                json.dumps(processing_info),
            )
        extra = processing_info if flds.get("include_processing_info", False) else None
        rez = processing_info["result"]
        return self.action_result(
            result=rez.result if rez else None,
            rez=rez,
            flds=rez.flds if rez else {},
            extra=extra,
        )


class All(ListAction):
    """
    executes all actions
    """

    _all: str = "all"
    op_mode: ListOpMode = ListOpMode.ALL

    def execute(self, tag: str = None, rez: Rez = None):
        return super().execute(tag=tag, rez=rez)


class UntilSuccess(ListAction):
    """
    executes actions until first success
    """

    until_success: str = "until_success"
    op_mode: ListOpMode = ListOpMode.UNTIL_SUCCESS

    def execute(self, tag: str = None, rez: Rez = None):
        return super().execute(tag=tag, rez=rez)


class UntilFailure(ListAction):
    """
    executes actions until first failure
    """

    until_failure: str = "until_failure"
    op_mode: ListOpMode = ListOpMode.UNTIL_FAILURE

    def execute(self, tag: str = None, rez: Rez = None):
        return super().execute(tag=tag, rez=rez)


def process_actions(
    calling_object: Action,
    op_mode: ListOpMode,
    actions: List[Action],
    tag: str = None,
    rez: Rez = None,
    successful_actions: List[Dict[Any, Any]] = [],
    exception_actions: List[Dict[Any, Any]] = [],
    processing_count: int = 0,
    success_count: int = 0,
    exception_count: int = 0,
):
    """
    services the three action list classes, ALL, UNTIL_SUCCESS, and UNTIL_FAILURE
    """
    exceptions: List[Exception] = []
    loop_rez = rez
    for action in actions:
        exception = None
        try:
            loop_rez = action.execute(tag=tag, rez=loop_rez)
            log_action_result(
                calling_logger=logger,
                calling_object=calling_object,
                tag=tag,
                action=action,
                result=loop_rez,
            )
        except Exception as e:
            exception = e
            logger.exception(
                f"ListAction: tag ({tag}); error while executing action ({action}); loop data ({loop_rez})",
                exc_info=exception,
            )
        processing_count += 1
        if exception:
            exception_count += 1
            exception_dict = action.dict().copy()
            exception_dict.update({"exception": str(exception)})
            exception_actions.append(exception_dict)
            if isinstance(exception, TerminateSchedulerException):
                exception.value = processing_results(
                    Rez(result=str(exception)),
                    processing_count,
                    success_count,
                    exception_count,
                    successful_actions,
                    exception_actions,
                )
                raise exception
            if op_mode == ListOpMode.UNTIL_FAILURE:  # stop after first failure
                break
            loop_rez = Rez(result=exception_dict, rez=rez, flds=rez.flds if rez else {})
        else:
            success_count += 1
            successful_actions.append(action.dict())
            if op_mode == ListOpMode.UNTIL_SUCCESS:  # stop after first success
                break
    return processing_results(
        loop_rez,
        processing_count,
        success_count,
        exception_count,
        successful_actions,
        exception_actions,
    )


class IfElse(Action):
    """
    executes actions based on:

        if test_action is successful, executes if_action
        otherwise executes else_action

    """

    if_else: str = "if_else"
    test_action: Action
    else_action: Action
    if_action: Optional[Action] = None
    exception_on_no_success: Optional[bool] = None
    include_processing_info: Optional[bool] = None

    def logger_info(self, s: str):
        logger.info(s)

    def logger_exception(self, s: str, exc_info: object):
        logger.info(s, exc_info)

    def description(self):
        return f"If  action ({self.test_action}) succeeds, then IfElse executes ({self.if_action}), otherwise executes ({self.else_action})"

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        test_action = flds["test_action"]
        else_action = flds["else_action"]
        if_action = flds.get("if_action", None)
        exception_on_no_success = flds.get("exception_on_no_success", False)
        include_processing_info = flds.get("include_processing_info", False)
        exception = None
        try:
            rez = test_action.execute(tag=tag, rez=rez)
            log_action_result(
                calling_logger=logger,
                calling_object=self,
                tag=tag,
                action=test_action,
                result=rez,
            )
        except Exception as e:
            exception = e
            self.logger_exception(
                f"IfElse: tag ({tag}); error while executing 'test' action ({test_action}) exception ({exception})",
                exc_info=exception,
            )
        processing_count = 1
        success_count = 0
        exception_count = 0
        successful_actions: List[Dict[Any, Any]] = []
        exception_actions: List[Dict[Any, Any]] = []
        if exception:  # execute the else action
            exception_count = 1
            exception_dict = test_action.dict().copy()
            exception_dict.update({"exception": str(exception)})
            exception_actions.append(exception_dict)
            if isinstance(exception, TerminateSchedulerException):
                exception.value = processing_results(
                    rez,
                    processing_count,
                    success_count,
                    exception_count,
                    successful_actions,
                    exception_actions,
                )
                raise exception
            exception = None
            try:
                rez = else_action.execute(tag=tag, rez=rez)
                log_action_result(
                    calling_logger=logger,
                    calling_object=self,
                    tag=tag,
                    action=else_action,
                    result=rez,
                )
            except Exception as e:
                exception = e
                self.logger_exception(
                    f"IfElse: tag ({tag}); error while executing 'else' action ({else_action}) exception ({exception})",
                    exc_info=exception,
                )
            processing_count += 1
            if exception:
                exception_count += 1
                exception_dict = else_action.dict().copy()
                exception_dict.update({"exception": str(exception)})
                exception_actions.append(exception_dict)
                if isinstance(exception, TerminateSchedulerException):
                    exception.value = processing_results(
                        rez,
                        processing_count,
                        success_count,
                        exception_count,
                        successful_actions,
                        exception_actions,
                    )
                    raise exception
                rez = self.action_result(
                    result=exception_dict, rez=rez, flds=rez.flds if rez else {}
                )
            else:
                success_count += 1
                successful_actions.append(else_action.dict())
        else:
            success_count += 1
            successful_actions.append(test_action.dict())

            if if_action:  # execute the if_action
                exception = None
                try:
                    rez = if_action.execute(tag=tag, rez=rez)
                    log_action_result(
                        calling_logger=logger,
                        calling_object=self,
                        tag=tag,
                        action=if_action,
                        result=rez,
                    )
                except Exception as e:
                    exception = e
                    self.logger_exception(
                        f"IfElse: tag ({tag}); error while executing 'if' action ({else_action}) exception ({exception})",
                        exc_info=exception,
                    )
                processing_count += 1
                if exception:
                    exception_count += 1
                    exception_dict = if_action.dict().copy()
                    exception_dict.update({"exception": str(exception)})
                    exception_actions.append(exception_dict)
                    if isinstance(exception, TerminateSchedulerException):
                        exception.value = processing_results(
                            rez,
                            processing_count,
                            success_count,
                            exception_count,
                            successful_actions,
                            exception_actions,
                        )
                        raise exception
                    rez = self.action_result(
                        result=exception_dict, rez=rez, flds=rez.flds if rez else {}
                    )
                else:
                    success_count += 1
                    successful_actions.append(if_action.dict())
            else:  # just use test_result since there is no if_action
                pass

        processing_info = processing_results(
            rez,
            processing_count,
            success_count,
            exception_count,
            successful_actions,
            exception_actions,
        )
        if (
            processing_info["processing_count"] > 0
            and processing_info["success_count"] == 0
            and exception_on_no_success
        ):
            raise Exception(
                "exception generated; all actions failing treated as an if-else action failure",
                json.dumps(self.dict()),
                json.dumps(processing_info),
            )
        extra = processing_info if include_processing_info else None
        rez = processing_info["result"]
        return self.action_result(
            result=rez.result if rez else None,
            rez=rez,
            flds=rez.flds if rez else {},
            extra=extra,
        )


class FormatOpMode(str, Enum):
    FLATTEN = "flatten"
    FIRST = "first"


class RezFmt(Action):
    rez_fmt: str = "rez_fmt"
    format_op_mode: Optional[FormatOpMode] = None

    def description(self):
        return f"Transforms Rez results recursively into a list structure or uses just the top-level rez."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        op_mode = flds.get("format_op_mode", FormatOpMode.FLATTEN)
        if rez is not None:
            if op_mode == FormatOpMode.FLATTEN:
                result = rez.flatten_results()
            else:
                result = rez.flatten_result()
        else:
            result = "Incoming Rez is empty."
        return self.action_result(
            result=result,
            rez=rez,
            flds=rez.flds if rez else {},
        )


# experimental


class Compose(Action):
    compose: str = "compose"
    actions: List[Action]

    def description(self):
        return (
            f"Performs function composition on supplied actions in left-to-right order."
        )

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        actions = flds["actions"]
        loop_rez = rez
        for action in actions:
            loop_rez = action.execute(tag=tag, rez=loop_rez)
            log_action_result(
                calling_logger=logger,
                calling_object=self,
                tag=tag,
                action=action,
                result=loop_rez,
            )
        return loop_rez
