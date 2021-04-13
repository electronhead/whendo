import pytest
from datetime import datetime, timedelta
from whendo.core.util import Now
from whendo.core.scheduling import DeferredProgram, DeferredPrograms, ScheduledActions


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


def test_scheduled_actions_1():
    sas = ScheduledActions()
    sas.add("bar", "foo")
    sas.add("blee", "flea")
    sas.add("blee", "tea")
    sas.add("why", "flea")

    assert len(sas.actions("bar")) == 1
    assert len(sas.actions("blee")) == 2
    assert len(sas.actions("why")) == 1
    assert sas.action_count() == 3
    assert sas.actions("blee") == set(["flea", "tea"])
    assert sas.action_names() == {"foo", "flea", "tea"}

    sas.delete_scheduler("blee")
    assert sas.action_count() == 2
