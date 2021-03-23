import whendo.core.actions.logic_action as logic_x
from whendo.core.action import Action
import pytest


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


def test_if_else_action_or_2():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__
            return True

    class Action2(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__
            return True

    class Action3(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__
            return True

    if_else_action = logic_x.IfElse(
        test_action=Action1(),
        else_action=Action2(),
        if_action=Action3(),
        exception_on_no_success=False,
    )
    result = if_else_action.execute()
    assert dictionary["value"] == Action3


def test_if_else_action_else_1():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            return Exception()

    class Action2(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__
            return True

    class Action3(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__
            return True

    if_else_action = logic_x.IfElse(
        test_action=Action1(),
        else_action=Action2(),
        if_action=Action3(),
        exception_on_no_success=False,
    )
    result = if_else_action.execute()
    assert dictionary["value"] == Action2


def test_if_else_action_else_2():
    """
    Show that, in the absence of an if_action,
    if test action succeeds, its result
    is the result of if_then_else.
    """
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__
            return Exception()

    class Action2(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__
            return True

    if_else_action = logic_x.IfElse(
        test_action=Action1(),
        else_action=Action2(),
        exception_on_no_success=False,
    )
    result = if_else_action.execute()
    assert dictionary["value"] == Action2


def test_if_else_action_else_3():
    """
    Show that, in the absence of an if_action,
    if test action fails, the else result
    is the result of if_then_else.
    """
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__
            return True

    class Action2(Action):
        def execute(self, tag: str = None, data: dict = None):
            dictionary["value"] = self.__class__
            return True

    if_else_action = logic_x.IfElse(
        test_action=Action1(),
        else_action=Action2(),
        exception_on_no_success=False,
    )
    result = if_else_action.execute()
    assert dictionary["value"] == Action1


def test_composition_all_1():
    """
    Show that Actions execute methods are composed.
    """

    class Add1(Action):
        def execute(self, tag: str = None, data: dict = None):
            if data:
                value = data.get("result", 0)
                if isinstance(value, int) or isinstance(value, float):
                    return 1 + value
            return 1

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

    class Add1(Action):
        def execute(self, tag: str = None, data: dict = None):
            if data:
                value = data.get("result", 0)
                if isinstance(value, int) or isinstance(value, float):
                    return 1 + value
            return 1

    add1 = Add1()
    sum_all = logic_x.All(actions=[add1, add1, logic_x.Failure(), add1, add1]).execute(
        data={"result": 10.1}
    )
    assert sum_all["result"] == 2


def test_composition_all_3():
    """
    Show that introduction of Success does not impact the result.
    """

    class Add1(Action):
        def execute(self, tag: str = None, data: dict = None):
            if data:
                value = data.get("result", 0)
                if isinstance(value, int) or isinstance(value, float):
                    return 1 + value
            return 1

    add1 = Add1()
    sum_all = logic_x.All(actions=[add1, add1, logic_x.Success(), add1, add1]).execute(
        data={"result": 10.1}
    )
    assert sum_all["result"] == 14.1


def test_composition_and():
    """
    Show that composition stops at the first failure.
    """

    class Add1(Action):
        def execute(self, tag: str = None, data: dict = None):
            if data:
                value = data.get("result", 0)
                if isinstance(value, int) or isinstance(value, float):
                    return 1 + value
            return 1

    add1 = Add1()
    sum_and = logic_x.And(actions=[add1, add1, logic_x.Failure(), add1, add1]).execute(
        data={"result": 10.1}
    )
    assert sum_and["result"] == 12.1


def test_composition_or():
    """
    Show that composition stops at the first success.
    """

    class Add1(Action):
        def execute(self, tag: str = None, data: dict = None):
            if data:
                value = data.get("result", 0)
                if isinstance(value, int) or isinstance(value, float):
                    return 1 + value
            return 1

    add1 = Add1()
    sum_or = logic_x.Or(actions=[add1, add1, logic_x.Failure(), add1, add1]).execute(
        data={"result": 10.1}
    )
    assert sum_or["result"] == 11.1


def test_composition_arg():
    """
    Show that inserting Arg has same effect as passing a value to the execute method.
    """

    class Add1(Action):
        def execute(self, tag: str = None, data: dict = None):
            if data:
                value = data.get("result", 0)
                if isinstance(value, int) or isinstance(value, float):
                    return 1 + value
            return 1

    add1 = Add1()
    sum_all = logic_x.All(
        actions=[logic_x.Arg(data={"result": 10.1}), add1, add1, add1]
    ).execute()
    assert sum_all["result"] == 13.1


def test_compose():
    """
    Show that Compose composes function results.
    """

    class Add1(Action):
        def execute(self, tag: str = None, data: dict = None):
            if isinstance(data, dict):
                value = data.get("result", 0)
                if isinstance(value, int) or isinstance(value, float):
                    return {"result": 1 + value}
            return {"result": 1}

    add1 = Add1()
    result = logic_x.Compose(actions=[add1, add1, logic_x.Success(), add1]).execute()
    assert result["result"] == 3
