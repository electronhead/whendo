import pytest
from datetime import datetime, timedelta
from whendo.core.program import ProgramItem
from whendo.core.programs.simple_program import PBEProgram
from whendo.core.util import Now
from whendo.core.scheduling import DeferredProgram, DeferredPrograms


def test_program_1():
    program = PBEProgram(
        prologue_name="foo1", epilogue_name="foo100", body={"bar": ["foo3", "foo4"]}
    )
    assert program.prologue_name == "foo1"
    assert program.epilogue_name == "foo100"
    assert program.body == {"bar": ["foo3", "foo4"]}


def test_program_2():
    program = (
        PBEProgram()
        .prologue("foo1")
        .epilogue("foo100")
        .body_element("bar", "foo3")
        .body_element("bar", "foo4")
    )
    assert program.prologue_name == "foo1"
    assert program.epilogue_name == "foo100"
    assert program.body == {"bar": ["foo3", "foo4"]}


def test_program_3():
    program1 = (
        PBEProgram()
        .prologue("foo1")
        .epilogue("foo100")
        .body_element("bar", "foo3")
        .body_element("bar", "foo4")
    )
    program2 = PBEProgram(
        body={"bar": ["foo3", "foo4"]}, epilogue_name="foo100", prologue_name="foo1"
    )
    assert program1 == program2


def test_program_item_1():
    dt = Now.dt()
    scheduler_name = "bar"
    action_name = "foo"
    typ = "defer"
    item = ProgramItem(typ, dt, scheduler_name, action_name)
    assert item.type == typ
    assert item.dt == dt
    assert item.scheduler_name == scheduler_name
    assert item.action_name == action_name


def test_program_item_2():
    dt = None
    scheduler_name = "bar"
    action_name = "foo"
    typ = "defer"
    item = ProgramItem(typ, dt, scheduler_name, action_name)
    assert item.dt is None

def test_deferred_program_1():
    """
    Comparing operations on copies.
    """
    dt1 = Now.dt()
    dt2 = dt1 + timedelta(seconds=10)
    prog = DeferredProgram("baz", dt1, dt2)

    progs = DeferredPrograms()
    progs.add(prog)
    progs2 = progs.copy()

    assert progs.count() == 1
    popped = progs.pop()
    assert len(popped) == 1
    assert list(popped)[0] == prog
    assert progs.count() == 0

    assert progs2.count() == 1
    popped2 = progs2.pop()
    assert len(popped2) == 1
    assert list(popped2)[0] == prog
    assert progs2.count() == 0

def test_deferred_program_2():
    """
    Testing 'clear' method.
    """
    dt1 = Now.dt()
    dt2 = dt1 + timedelta(seconds=10)
    prog = DeferredProgram("baz", dt1, dt2)

    progs = DeferredPrograms()
    progs.add(prog)
    
    progs.clear()

    assert progs.count() == 0

def test_deferred_program_3():
    """
    Testing 'clear_program' method.
    """
    dt1 = Now.dt()
    dt2 = dt1 + timedelta(seconds=10)
    prog = DeferredProgram("baz", dt1, dt2)

    progs = DeferredPrograms()
    progs.add(prog)
    
    progs.clear_program("baz")

    assert progs.count() == 0