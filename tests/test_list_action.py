from typing import Optional, Any, Dict
import pytest
import whendo.core.actions.list_action as list_x
from whendo.core.action import Action, Rez
from whendo.core.exception import TerminateSchedulerException


def negate(action: Action):
    return list_x.Fail(operand=action)


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
    assert not computes_exception(list_x.Success().execute)


def test_exception_1():
    assert computes_exception(list_x.Failure().execute)


def test_not_1():
    class Action1(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            raise Exception()

    action1 = Action1()
    action2 = negate(action1)
    action3 = negate(action2)
    assert computes_exception(action1.execute)
    assert not computes_exception(action2.execute)
    assert computes_exception(action3.execute)


def test_not_2():
    class Action1(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            return self.action_result()

    action1 = Action1()
    action2 = negate(action1)
    action3 = negate(action2)
    assert not computes_exception(action1.execute)
    assert computes_exception(action2.execute)
    assert not computes_exception(action3.execute)


def test_vals_1():
    class Action1(Action):
        n: Optional[int] = None

        def execute(self, tag: str = None, rez: Rez = None):
            assert rez
            assert rez.flds
            flds = self.compute_flds(rez=rez)
            assert "n" in flds
            n = flds["n"]
            return self.action_result(result=n)

    action1 = Action1()
    action2 = list_x.Vals(vals={"n": 137})
    action3 = list_x.All(actions=[action2, action1])
    result = action3.execute()
    assert result.result == 137


def test_vals_2():
    class Action1(Action):
        n: Optional[int] = None
        m: Optional[int] = None

        def execute(self, tag: str = None, rez: Rez = None):
            assert rez
            assert rez.flds
            flds = self.compute_flds(rez=rez)
            assert "n" in flds
            assert "m" in flds
            n = flds["n"]
            m = flds["m"]
            return self.action_result(result=n * m)

    action1 = Action1()
    action2 = list_x.Vals(vals={"n": 137})
    action3 = list_x.Vals(vals={"m": 2})
    action3 = list_x.All(actions=[action3, action2, action1])
    result = action3.execute()
    assert result.result == 137 * 2


def test_list_action_all_1():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action2(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action3(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action4(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    all_action = list_x.All(
        op_mode=list_x.ListOpMode.ALL,
        actions=[Action1(), Action2(), Action3(), Action4()],
    )
    result = all_action.execute()
    assert dictionary["value"] == Action4


def test_list_action_us_1():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action2(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action3(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action4(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    us_action = list_x.UntilSuccess(
        actions=[negate(Action1()), Action2(), Action3(), Action4()],
    )
    result = us_action.execute()
    assert dictionary["value"] == Action2


def test_list_action_uf_1():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action2(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action3(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action4(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    uf_action = list_x.UntilFailure(
        actions=[Action1(), Action2(), Action3(), Action4()],
    )
    result = uf_action.execute()
    assert dictionary["value"] == Action4


def test_list_action_uf_2():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action2(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action3(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    class Action4(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__

    uf_action = list_x.UntilFailure(
        actions=[
            negate(Action1()),
            negate(Action2()),
            negate(Action3()),
            negate(Action4()),
        ]
    )
    result = uf_action.execute()
    assert dictionary["value"] == Action1


def test_list_action_uf_3():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            return Exception()

    class Action2(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            return Exception()

    class Action3(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            return Exception()

    class Action4(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            return Exception()

    uf_action = list_x.UntilFailure(
        actions=[Action1(), Action2(), Action3(), Action4()],
        exception_on_no_success=True,
    )
    assert computes_exception(uf_action.execute)


def test_if_else_action_else_1():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            raise Exception()

    class Action2(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__
            return self.action_result()

    class Action3(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__
            return self.action_result()

    if_else_action = list_x.IfElse(
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
    is the result of else_action.
    """
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__
            raise Exception()

    class Action2(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__
            return self.action_result()

    if_else_action = list_x.IfElse(
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
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__
            return self.action_result()

    class Action2(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__
            return self.action_result()

    if_else_action = list_x.IfElse(
        test_action=Action1(),
        else_action=Action2(),
        exception_on_no_success=False,
    )
    result = if_else_action.execute()
    assert dictionary["value"] == Action1


def test_if_else_action_4():
    dictionary = {"value": None}

    class Action1(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__
            return self.action_result()

    class Action2(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__
            return self.action_result()

    class Action3(Action):
        def execute(self, tag: str = None, rez: Rez = None):
            dictionary["value"] = self.__class__
            return self.action_result()

    if_else_action = list_x.IfElse(
        test_action=Action1(),
        else_action=Action2(),
        if_action=Action3(),
        exception_on_no_success=False,
    )
    result = if_else_action.execute()
    assert dictionary["value"] == Action3


def test_composition_all_1():
    """
    Show that Actions execute methods are composed.
    """
    add1 = Add1()
    sum_all = list_x.All(actions=[add1, add1, add1, add1]).execute(rez=Rez(result=10.1))
    assert sum_all.result == 14.1


def test_composition_all_2():
    """
    Show that introduction of a Failure in All essentially starts
    things over again.
    """
    add1 = Add1()
    sum_all = list_x.All(actions=[add1, add1, list_x.Failure(), add1, add1]).execute(
        rez=Rez(result=10.1)
    )
    assert sum_all.result == 2


def test_composition_all_3():
    """
    Show that introduction of Success does not impact the result.
    """
    add1 = Add1()
    sum_all = list_x.All(actions=[add1, add1, list_x.Success(), add1, add1]).execute(
        rez=Rez(result=10.1)
    )
    assert sum_all.result == 14.1


def test_composition_uf():
    """
    Show that composition stops at the first failure.
    """
    add1 = Add1()
    sum_uf = list_x.UntilFailure(
        actions=[add1, add1, list_x.Failure(), add1, add1]
    ).execute(rez=Rez(result=10.1))
    assert sum_uf.result == 12.1


def test_composition_us():
    """
    Show that composition stops at the first success.
    """
    add1 = Add1()
    sum_us = list_x.UntilSuccess(
        actions=[add1, add1, list_x.Failure(), add1, add1]
    ).execute(rez=Rez(result=10.1))
    assert sum_us.result == 11.1


def test_composition_arg():
    """
    Show that inserting Arg has same effect as passing a value to the execute method.
    """
    add1 = Add1()
    sum_all = list_x.All(
        actions=[list_x.Result(value=10.1), add1, add1, add1]
    ).execute()
    assert sum_all.result == 13.1


def test_compose():
    """
    Show that Compose composes function results.
    """
    add1 = Add1()
    result = list_x.Compose(actions=[add1, add1, list_x.Success(), add1]).execute()
    assert result.result == 3


def test_terminate():
    class FleaCount(Action):
        flea_count: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.flea_count += 1
            return self.action_result(result=self.flea_count)

    action1 = FleaCount(flea_count=0)
    action2 = FleaCount(flea_count=0)
    actions = [action1, list_x.Terminate(), action2]
    action3 = list_x.UntilFailure()  # pydantic copies actions list in the constructor
    action3.actions = actions
    with pytest.raises(TerminateSchedulerException):
        result = action3.execute()
    assert action1.flea_count == 1
    assert action2.flea_count == 0


def test_raise_cmp_1():
    """
    Show that raising stops processing of the list action.
    """
    add1 = Add1()
    result = list_x.UntilFailure(
        include_processing_info=True,
        actions=[add1, add1, list_x.RaiseCmp(cmp=0, value=2), add1, add1],
    ).execute()
    assert result.result == 2


def test_raise_cmp_2():
    """
    Show that not raising has no effect on the passing of results to the last action.
    """
    add1 = Add1()
    result = list_x.UntilFailure(
        actions=[add1, add1, list_x.RaiseCmp(cmp=0, value=1), add1, add1]
    ).execute()
    assert result.result == 4


def test_raise_cmp_3():
    """
    Show that not raising has no effect on the passing of results to the last action.
    """
    add1 = Add1()
    result = list_x.UntilFailure(
        actions=[
            list_x.Result(value=2),
            list_x.RaiseCmp(cmp=0, value=2),
            add1,
            add1,
        ]
    ).execute()
    assert result.result == 2


def test_raise_cmp_4():
    """
    Show that not raising has no effect on the passing of results to the last action.
    """
    add1 = Add1()
    result = list_x.UntilFailure(
        actions=[
            list_x.Result(value=2),
            list_x.RaiseCmp(cmp=0, value=1),
            add1,
            add1,
        ]
    ).execute()
    assert result.result == 4


def test_raise_cmp_5():
    """
    Show that raising stops processing of the list action.
    """
    add1 = Add1()
    result = list_x.UntilFailure(
        include_processing_info=True,
        actions=[add1, add1, list_x.RaiseCmp(cmp=-1, value=3), add1, add1],
    ).execute()
    assert result.result == 2


def test_raise_cmp_6():
    """
    Show that not raising has no effect on the passing of results to the last action.
    """
    add1 = Add1()
    result = list_x.UntilFailure(
        actions=[add1, add1, list_x.RaiseCmp(cmp=-1, value=2), add1, add1]
    ).execute()
    assert result.result == 4


def test_raise_cmp_7():
    """
    Show that not raising has no effect on the passing of results to the last action.
    """
    add1 = Add1()
    result = list_x.UntilFailure(
        actions=[
            list_x.Result(value=2),
            list_x.RaiseCmp(cmp=1, value=1),
            add1,
            add1,
        ]
    ).execute()
    assert result.result == 2


def test_raise_cmp_8():
    """
    Show that not raising has no effect on the passing of results to the last action.
    """
    add1 = Add1()
    result = list_x.UntilFailure(
        actions=[
            list_x.Result(value=2),
            list_x.RaiseCmp(cmp=1, value=3),
            add1,
            add1,
        ]
    ).execute()
    assert result.result == 4


# helpers


class Add1(Action):
    add_1: str = "add_1"

    def execute(self, tag: str = None, rez: Rez = None):
        if rez:
            if isinstance(rez.result, int) or isinstance(rez.result, float):
                return self.action_result(result=rez.result + 1)
        return self.action_result(result=1)
