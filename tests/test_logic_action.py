from typing import Optional, Any, Dict
import pytest
import whendo.core.actions.logic_action as logic_x
from whendo.core.action import Action
from whendo.core.exception import TerminateSchedulerException


def negate(action: Action):
    return logic_x.Not(operand=action)


def is_exception(result):
    return isinstance(result, Exception)


def computes_exception(thunk):
    try:
        result = thunk()
    except Exception as exception:
        result = exception
    return isinstance(result, Exception)


# =================== tests ==================?


def test_success_1():
    assert not computes_exception(logic_x.Success().execute)


def test_exception_1():
    assert computes_exception(logic_x.Failure().execute)


def test_not_1():
    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            raise Exception()

    action1 = Action1()
    action2 = negate(action1)
    action3 = negate(action2)
    assert computes_exception(action1.execute)
    assert not computes_exception(action2.execute)
    assert computes_exception(action3.execute)


def test_not_2():
    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            return True

    action1 = Action1()
    action2 = negate(action1)
    action3 = negate(action2)
    assert not computes_exception(action1.execute)
    assert computes_exception(action2.execute)
    assert not computes_exception(action3.execute)


def test_list_action_all_1():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action2(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action3(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action4(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    all_action = logic_x.All(
        op_mode=logic_x.ListOpMode.ALL,
        actions=[Action1(), Action2(), Action3(), Action4()],
    )
    result = all_action.execute()
    assert dictionary["value"] == Action4


def test_list_action_or_1():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action2(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action3(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action4(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    or_action = logic_x.Or(
        actions=[negate(Action1()), Action2(), Action3(), Action4()],
    )
    result = or_action.execute()
    assert dictionary["value"] == Action2


def test_list_action_and_1():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action2(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action3(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action4(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    and_action = logic_x.And(
        actions=[Action1(), Action2(), Action3(), Action4()],
    )
    result = and_action.execute()
    assert dictionary["value"] == Action4


def test_list_action_and_2():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action2(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action3(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    class Action4(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__

    and_action = logic_x.And(
        actions=[
            negate(Action1()),
            negate(Action2()),
            negate(Action3()),
            negate(Action4()),
        ]
    )
    result = and_action.execute()
    assert dictionary["value"] == Action1


def test_list_action_and_3():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            return Exception()

    class Action2(Action):
        def execute(self, tag: str = None, data: dict = None):
            return Exception()

    class Action3(Action):
        def execute(self, tag: str = None, data: dict = None):
            return Exception()

    class Action4(Action):
        def execute(self, tag: str = None, data: dict = None):
            return Exception()

    and_action = logic_x.And(
        actions=[Action1(), Action2(), Action3(), Action4()],
        exception_on_no_success=True,
    )
    assert computes_exception(and_action.execute)


def test_composition_all_1():
    """
    Show that Actions execute methods are composed.
    """
    add1 = Add1()
    sum_all = logic_x.All(actions=[add1, add1, add1, add1]).execute(
        data={"result": 10.1}
    )
    assert sum_all["result"] == 14.1


def test_composition_all_2():
    """
    Show that introduction of a Failure in All essentially starts
    things over again.
    """
    add1 = Add1()
    sum_all = logic_x.All(actions=[add1, add1, logic_x.Failure(), add1, add1]).execute(
        data={"result": 10.1}
    )
    assert sum_all["result"] == 2


def test_composition_all_3():
    """
    Show that introduction of Success does not impact the result.
    """
    add1 = Add1()
    sum_all = logic_x.All(actions=[add1, add1, logic_x.Success(), add1, add1]).execute(
        data={"result": 10.1}
    )
    assert sum_all["result"] == 14.1


def test_composition_and():
    """
    Show that composition stops at the first failure.
    """
    add1 = Add1()
    sum_and = logic_x.And(actions=[add1, add1, logic_x.Failure(), add1, add1]).execute(
        data={"result": 10.1}
    )
    print(sum_and)
    assert sum_and["result"] == 12.1


def test_composition_or():
    """
    Show that composition stops at the first success.
    """
    add1 = Add1()
    sum_or = logic_x.Or(actions=[add1, add1, logic_x.Failure(), add1, add1]).execute(
        data={"result": 10.1}
    )
    assert sum_or["result"] == 11.1


def test_composition_arg():
    """
    Show that inserting Arg has same effect as passing a value to the execute method.
    """
    add1 = Add1()
    sum_all = logic_x.All(
        actions=[logic_x.Arg(data={"result": 10.1}), add1, add1, add1]
    ).execute()
    print("sum_all", sum_all)
    assert sum_all["result"] == 13.1


def test_compose():
    """
    Show that Compose composes function results.
    """
    add1 = Add1()
    result = logic_x.Compose(actions=[add1, add1, logic_x.Success(), add1]).execute()
    assert result["result"] == 3


def test_terminate():
    class FleaCount(Action):
        flea_count: int = 0

        def execute(self, tag: str = None, data: dict = None):
            self.flea_count += 1
            return self.action_result(result=self.flea_count, data=data)

    action1 = FleaCount(flea_count=0)
    action2 = FleaCount(flea_count=0)
    actions = [action1, logic_x.Terminate(), action2]
    action3 = logic_x.And()  # pydantic copies actions list in the constructor
    action3.actions = actions
    with pytest.raises(TerminateSchedulerException):
        result = action3.execute()
    assert action1.flea_count == 1
    assert action2.flea_count == 0


def test_raise_if_equal_1():
    """
    Show that raising stops processing of the list action.
    """
    add1 = Add1()
    result = logic_x.And(
        include_processing_info=True,
        actions=[add1, add1, logic_x.RaiseIfEqual(value=2), add1, add1],
    ).execute()
    print(result)
    assert result["result"] == 2


def test_raise_if_equal_2():
    """
    Show that not raising has no effect on the passing of results to the last action.
    """
    add1 = Add1()
    result = logic_x.And(
        actions=[add1, add1, logic_x.RaiseIfEqual(value=1), add1, add1]
    ).execute()
    assert result["result"] == 4


def test_raise_if_equal_3():
    """
    Show that not raising has no effect on the passing of results to the last action.
    """
    add1 = Add1()
    result = logic_x.And(
        actions=[
            logic_x.Arg(data={"result": 2}),
            logic_x.RaiseIfEqual(value=2),
            add1,
            add1,
        ]
    ).execute()
    assert result["result"] == 2


def test_raise_if_equal_4():
    """
    Show that not raising has no effect on the passing of results to the last action.
    """
    add1 = Add1()
    result = logic_x.And(
        actions=[
            logic_x.Arg(data={"result": 2}),
            logic_x.RaiseIfEqual(value=1),
            add1,
            add1,
        ]
    ).execute()
    assert result["result"] == 4


# helpers


class Add1(Action):
    add_1: str = "add_1"

    def execute(self, tag: str = None, data: dict = None):
        if isinstance(data, dict):
            value = self.get_result(data)
            if isinstance(value, int) or isinstance(value, float):
                return self.action_result(result=1 + value, data=data)
        return self.action_result(result=1, data=data)
