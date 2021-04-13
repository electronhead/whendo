import pytest
from datetime import datetime
from whendo.core.program import ProgramItem
from whendo.core.programs.simple_program import PBEProgram
from whendo.core.util import Now


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
