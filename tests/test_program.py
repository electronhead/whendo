import pytest
from whendo.core.program import Program


def test_program_1():
    program = Program(
        prologue_name="foo1", epilogue_name="foo100", body={"bar": ["foo3", "foo4"]}
    )
    assert program.prologue_name == "foo1"
    assert program.epilogue_name == "foo100"
    assert program.body == {"bar": ["foo3", "foo4"]}


def test_program_2():
    program = (
        Program()
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
        Program()
        .prologue("foo1")
        .epilogue("foo100")
        .body_element("bar", "foo3")
        .body_element("bar", "foo4")
    )
    program2 = Program(
        body={"bar": ["foo3", "foo4"]}, epilogue_name="foo100", prologue_name="foo1"
    )
    assert program1 == program2
