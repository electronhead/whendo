import pytest
import time
from datetime import timedelta
from typing import Optional, Dict, Any
from whendo.core.util import Rez, SystemInfo, Now, KeyTagMode, DateTime, Rez
from whendo.core.action import Action
from whendo.core.server import Server
from whendo.core.actions.list_action import (
    UntilFailure,
    All,
    Terminate,
    IfElse,
    RaiseCmp,
    Result,
)
from whendo.core.schedulers.timed_scheduler import Timely
from whendo.core.scheduler import Immediately
from whendo.core.dispatcher import Dispatcher
from whendo.core.programs.simple_program import PBEProgram
from whendo.core.actions.dispatch_action import (
    ScheduleProgram,
    UnscheduleProgram,
    ScheduleAction,
    DeferAction,
    ExpireAction,
)
from whendo.core.timed import Timed
from .fixtures import port, host

pause = 3


def test_server_all_1(friends, servers):
    dispatcher, scheduler, action = friends()
    aqua, teal = servers()
    dispatcher.add_server(server_name="aqua", server=aqua)
    dispatcher.add_server(server_name="teal", server=teal)
    mode = KeyTagMode.ALL
    result = dispatcher.get_servers_by_tags(
        key_tags={"foo": ["bar", "baz"]}, key_tag_mode=mode
    )
    assert len(result) == 2


def test_server_all_2(friends, servers):
    dispatcher, scheduler, action = friends()
    aqua, teal = servers()
    dispatcher.add_server(server_name="aqua", server=aqua)
    dispatcher.add_server(server_name="teal", server=teal)
    mode = KeyTagMode.ALL
    result = dispatcher.get_servers_by_tags(
        key_tags={"foo": ["bar"]}, key_tag_mode=mode
    )
    assert len(result) == 1


def test_server_all_3(friends, servers):
    dispatcher, scheduler, action = friends()
    aqua, teal = servers()
    dispatcher.add_server(server_name="aqua", server=aqua)
    dispatcher.add_server(server_name="teal", server=teal)
    mode = KeyTagMode.ALL
    result = dispatcher.get_servers_by_tags(key_tags={"foo": []}, key_tag_mode=mode)
    assert len(result) == 0


def test_server_all_4(friends, servers):
    dispatcher, scheduler, action = friends()
    aqua, teal = servers()
    dispatcher.add_server(server_name="aqua", server=aqua)
    dispatcher.add_server(server_name="teal", server=teal)
    mode = KeyTagMode.ALL
    result = dispatcher.get_servers_by_tags(
        key_tags={"foo": ["clasp"]}, key_tag_mode=mode
    )
    assert len(result) == 0


def test_server_any_1(friends, servers):
    dispatcher, scheduler, action = friends()
    aqua, teal = servers()
    dispatcher.add_server(server_name="aqua", server=aqua)
    dispatcher.add_server(server_name="teal", server=teal)
    mode = KeyTagMode.ANY
    result = dispatcher.get_servers_by_tags(
        key_tags={"foo": ["bar", "baz"]}, key_tag_mode=mode
    )
    assert len(result) == 2


def test_server_any_2(friends, servers):
    dispatcher, scheduler, action = friends()
    aqua, teal = servers()
    dispatcher.add_server(server_name="aqua", server=aqua)
    dispatcher.add_server(server_name="teal", server=teal)
    mode = KeyTagMode.ANY
    result = dispatcher.get_servers_by_tags(
        key_tags={"foo": ["bar"]}, key_tag_mode=mode
    )
    assert len(result) == 2


def test_server_any_3(friends, servers):
    dispatcher, scheduler, action = friends()
    aqua, teal = servers()
    dispatcher.add_server(server_name="aqua", server=aqua)
    dispatcher.add_server(server_name="teal", server=teal)
    mode = KeyTagMode.ANY
    result = dispatcher.get_servers_by_tags(key_tags={"foo": []}, key_tag_mode=mode)
    assert len(result) == 0


def test_server_any_4(friends, servers):
    dispatcher, scheduler, action = friends()
    aqua, teal = servers()
    dispatcher.add_server(server_name="aqua", server=aqua)
    dispatcher.add_server(server_name="teal", server=teal)
    mode = KeyTagMode.ANY
    result = dispatcher.get_servers_by_tags(
        key_tags={"foo": ["clasp"]}, key_tag_mode=mode
    )
    assert len(result) == 0


def test_schedule_action(friends):
    """
    Tests Dispatcher and Timed objects running a scheduled action.
    """
    dispatcher, scheduler, action = friends()

    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action("bar", "foo")

    assert dispatcher.get_scheduled_action_count() == 1

    dispatcher.run_jobs()
    time.sleep(pause)
    dispatcher.stop_jobs()
    dispatcher.clear_jobs()

    assert action.flea_count > 0


def test_schedule_action_action(friends):
    """
    Tests Dispatcher and Timed objects running a scheduled action.
    """
    dispatcher, scheduler, action = friends()

    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    schedule_action = ScheduleAction(scheduler_name="bar", action_name="foo")
    schedule_action.execute()

    assert dispatcher.get_scheduled_action_count() == 1

    dispatcher.run_jobs()
    time.sleep(pause)
    dispatcher.stop_jobs()
    dispatcher.clear_jobs()

    assert action.flea_count > 0


# def test_dispatcher_action_args_1(friends):
#     """
#     Tests computation of args based on fields, data and mode (=field).
#     """
#     dispatcher, scheduler, action = friends()
#     action2 = FleaCount(flea_count=100)

#     dispatcher.add_action("foo", action)
#     dispatcher.add_action("flea", action2)
#     dispatcher.add_scheduler("bar", scheduler)
#     schedule_action = ScheduleAction(
#         scheduler_name="bar", action_name="foo", mode=DispActionMode.FIELD
#     )
#     args = schedule_action.compute_args(
#         args={"scheduler_name": "bar", "action_name": "foo"},
#         data={"action_name": "flea"},
#     )
#     assert args["scheduler_name"] == "bar"
#     assert args["action_name"] == "foo"


# def test_dispatcher_action_args_2(friends):
#     """
#     Tests computation of args based on fields, data and mode (=data).
#     """
#     dispatcher, scheduler, action = friends()
#     action2 = FleaCount(flea_count=100)

#     dispatcher.add_action("foo", action)
#     dispatcher.add_action("flea", action2)
#     dispatcher.add_scheduler("bar", scheduler)
#     schedule_action = ScheduleAction(
#         scheduler_name="bar", action_name="foo", mode=DispActionMode.DATA
#     )
#     args = schedule_action.compute_args(
#         args={"scheduler_name": "bar", "action_name": "foo"},
#         data={"action_name": "flea"},
#     )
#     assert args["scheduler_name"] == "bar"
#     assert args["action_name"] == "flea"


# def test_dispatcher_action_args_3(friends):
#     """
#     Tests computation of args based on fields, data and mode (=field).
#     """
#     dispatcher, scheduler, action = friends()
#     action2 = FleaCount(flea_count=100)

#     dispatcher.add_action("foo", action)
#     dispatcher.add_action("flea", action2)
#     dispatcher.add_scheduler("bar", scheduler)
#     schedule_action = ScheduleAction(
#         scheduler_name="bar", action_name="foo", mode=DispActionMode.FIELD
#     )
#     args = schedule_action.compute_args(
#         args={"scheduler_name": "bar", "action_name": "foo"},
#         data={"result": {"action_name": "flea"}},
#     )
#     assert args["scheduler_name"] == "bar"
#     assert args["action_name"] == "foo"


# def test_dispatcher_action_args_4(friends):
#     """
#     Tests computation of args based on fields, data and mode (=data).
#     """
#     dispatcher, scheduler, action = friends()
#     action2 = FleaCount(flea_count=100)

#     dispatcher.add_action("foo", action)
#     dispatcher.add_action("flea", action2)
#     dispatcher.add_scheduler("bar", scheduler)
#     schedule_action = ScheduleAction(
#         scheduler_name="bar", action_name="foo", mode=DispActionMode.DATA
#     )
#     args = schedule_action.compute_args(
#         args={"scheduler_name": "bar", "action_name": "foo"},
#         data={"result": {"action_name": "flea"}},
#     )
#     assert args["scheduler_name"] == "bar"
#     assert args["action_name"] == "flea"


def test_schedule_action_action_data_1(friends):
    """
    Tests Dispatcher and Timed objects running a scheduled action.
    """
    dispatcher, scheduler, action = friends()
    action2 = FleaCount(flea_count=100)

    dispatcher.add_action("foo", action)
    dispatcher.add_action("flea", action2)
    dispatcher.add_scheduler("bar", scheduler)
    schedule_action = ScheduleAction(scheduler_name="bar", action_name="foo")
    schedule_action.execute(rez=Rez(flds={"action_name": "flea"}))

    assert dispatcher.get_scheduled_action_count() == 1

    dispatcher.run_jobs()
    time.sleep(pause)
    dispatcher.stop_jobs()
    dispatcher.clear_jobs()

    assert action.flea_count > 1
    assert action2.flea_count == 100


def test_schedule_action_action_data_2(friends):
    """
    Tests Dispatcher and Timed objects running a scheduled action.
    """
    dispatcher, scheduler, action = friends()
    action2 = FleaCount(flea_count=100)

    dispatcher.add_action("foo", action)
    dispatcher.add_action("flea", action2)
    dispatcher.add_scheduler("bar", scheduler)
    schedule_action = ScheduleAction(scheduler_name="bar")
    schedule_action.execute(rez=Rez(flds={"action_name": "flea"}))

    assert dispatcher.get_scheduled_action_count() == 1

    dispatcher.run_jobs()
    time.sleep(pause)
    dispatcher.stop_jobs()
    dispatcher.clear_jobs()

    assert action.flea_count == 0
    assert action2.flea_count > 100


def test_unschedule_scheduler(friends):
    """
    Tests unscheduling a scheduler.
    """
    dispatcher, scheduler, action = friends()
    assert dispatcher.job_count() == 0

    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action("bar", "foo")

    assert dispatcher.job_count() == 1

    dispatcher.unschedule_scheduler("bar")

    assert dispatcher.job_count() == 0
    assert dispatcher.get_scheduled_action_count() == dispatcher.job_count()

    # make sure that bar and foo remain
    assert dispatcher.get_scheduler("bar")
    assert dispatcher.get_action("foo")


def test_unschedule_all(friends):
    """
    Tests unscheduling all schedulers.
    """
    dispatcher, scheduler, action = friends()
    assert dispatcher.job_count() == 0

    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action("bar", "foo")
    assert dispatcher.job_count() == 1
    assert dispatcher.get_scheduled_action_count() == 1

    dispatcher.clear_jobs()
    assert dispatcher.job_count() == 0

    dispatcher.add_action("foo2", action)
    dispatcher.schedule_action("bar", "foo2")
    assert dispatcher.get_scheduled_action_count() == 2

    dispatcher.unschedule_all_schedulers()
    assert dispatcher.job_count() == 0
    assert dispatcher.get_scheduled_action_count() == 0


def test_reschedule_all(friends):
    """
    Tests unscheduling a scheduler.
    """
    dispatcher, scheduler, action = friends()
    assert dispatcher.job_count() == 0

    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action("bar", "foo")
    assert dispatcher.job_count() == 1
    assert dispatcher.get_scheduled_action_count() == 1

    dispatcher.clear_jobs()
    assert dispatcher.job_count() == 0

    dispatcher.add_action("foo2", action)
    dispatcher.schedule_action("bar", "foo2")
    assert dispatcher.get_scheduled_action_count() == 2

    dispatcher.reschedule_all_schedulers()
    assert dispatcher.job_count() == 1
    assert dispatcher.get_scheduled_action_count() == 2


def test_clear_dispatcher(friends):
    """
    Tests clearing a dispatcher.
    """
    dispatcher, scheduler, action = friends()
    assert dispatcher.job_count() == 0

    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action("bar", "foo")
    assert dispatcher.job_count() == 1

    dispatcher.clear_all()
    assert dispatcher.job_count() == 0
    assert dispatcher.get_scheduled_action_count() == dispatcher.job_count()

    # make sure that bar and foo are Gone
    assert dispatcher.get_scheduler("bar") is None
    assert dispatcher.get_action("foo") is None


def test_scheduled_action_count(friends):
    """
    Tests scheduled action count
    """
    # original
    dispatcher, scheduler, action = friends()
    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action(action_name="foo", scheduler_name="bar")
    assert 1 == dispatcher.get_scheduled_action_count()
    assert 1 == dispatcher.job_count()


def test_jobs_are_running(friends):
    dispatcher, scheduler, action = friends()
    try:
        dispatcher.run_jobs()
        assert dispatcher.jobs_are_running()
    finally:
        try:
            dispatcher.stop_jobs()
        except:
            pass


def test_jobs_are_not_running(friends):
    dispatcher, scheduler, action = friends()
    try:
        dispatcher.run_jobs()
        assert dispatcher.jobs_are_running()
        dispatcher.stop_jobs()
        assert not dispatcher.jobs_are_running()
    finally:
        try:
            dispatcher.stop_jobs()
        except:
            pass


def test_replace_dispatcher(friends):
    """
    Tests replacing a dispatcher
    """
    # original
    dispatcher, scheduler, action = friends()
    saved_dir = dispatcher.get_saved_dir()
    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action(action_name="foo", scheduler_name="bar")
    # replacement
    replacement = Dispatcher()  # no saved_dir
    replacement.add_action("flea", action)
    replacement.add_scheduler("bath", scheduler)
    replacement.schedule_action(action_name="flea", scheduler_name="bath")
    # do the business
    dispatcher.replace_all(replacement)
    # is everyone okay?
    assert not dispatcher.get_action("foo")
    assert not dispatcher.get_scheduler("bar")
    assert dispatcher.get_action("flea")
    assert dispatcher.get_scheduler("bath")
    assert {"bath"} == set(k for k in dispatcher.get_schedulers())
    assert {"flea"} == set(k for k in dispatcher.get_actions())
    assert {"bath"} == set(
        k for k in dispatcher.get_scheduled_actions().scheduler_names()
    )
    assert {"flea"} == dispatcher.get_scheduled_actions().actions("bath")


def test_load_dispatcher(friends):
    """
    Tests loading a dispatcher
    """
    dispatcher, scheduler, action = friends()
    saved_dir = dispatcher.get_saved_dir()
    assert saved_dir is not None
    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action(action_name="foo", scheduler_name="bar")
    dispatcher2 = dispatcher.load_current()
    assert dispatcher2 is not None, f"saved_dir({saved_dir})"
    assert set(k for k in dispatcher.get_actions()) == set(
        k for k in dispatcher2.get_actions()
    )
    assert set(k for k in dispatcher.get_schedulers()) == set(
        k for k in dispatcher2.get_schedulers()
    )
    assert set(k for k in dispatcher.get_scheduled_actions().action_names()) == set(
        k for k in dispatcher2.get_scheduled_actions().action_names()
    )


def test_saved_dir_1(tmp_path):
    saved_dir = str(tmp_path)
    dispatcher = Dispatcher()
    dispatcher.set_saved_dir(saved_dir=saved_dir)
    assert dispatcher.get_saved_dir() == saved_dir


def test_saved_dir_2(tmp_path):
    saved_dir = str(tmp_path)
    dispatcher = Dispatcher(saved_dir=saved_dir)
    assert dispatcher.get_saved_dir() == saved_dir


def test_defer_action(friends):
    """
    Want to observe the scheduling move from deferred state to ready state.
    """
    dispatcher, scheduler, action = friends()
    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)

    assert 0 == dispatcher.get_deferred_action_count()
    assert 0 == dispatcher.get_scheduled_action_count()

    dispatcher.defer_action(
        scheduler_name="bar", action_name="foo", wait_until=Now.dt()
    )

    # deferred state -- can run jobs and actions will _not_ be executed
    assert 1 == dispatcher.get_deferred_action_count()
    assert 0 == dispatcher.get_scheduled_action_count()

    time.sleep(6)  # the out-of-band job runs every five seconds

    # ready state -- can run jobs and actions will be executed
    assert 0 == dispatcher.get_deferred_action_count()
    assert 1 == dispatcher.get_scheduled_action_count()


def test_defer_action_action(friends):
    """
    Want to observe the scheduling move from deferred state to ready state.
    """
    dispatcher, scheduler, action = friends()
    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)

    assert 0 == dispatcher.get_deferred_action_count()
    assert 0 == dispatcher.get_scheduled_action_count()

    defer_action = DeferAction(
        scheduler_name="bar",
        action_name="foo",
        wait_until=DateTime(dt=Now.dt()),
    )
    defer_action.execute()

    # deferred state -- can run jobs and actions will _not_ be executed
    assert 1 == dispatcher.get_deferred_action_count()
    assert 0 == dispatcher.get_scheduled_action_count()

    time.sleep(6)  # the out-of-band job runs every five seconds

    # ready state -- can run jobs and actions will be executed
    assert 0 == dispatcher.get_deferred_action_count()
    assert 1 == dispatcher.get_scheduled_action_count()


def test_expire_action(friends):
    """
    Want to observe the scheduling move from deferred state to ready state.
    """
    dispatcher, scheduler, action = friends()
    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)

    assert 0 == dispatcher.get_expiring_action_count()
    assert 0 == dispatcher.get_scheduled_action_count()

    dispatcher.schedule_action(scheduler_name="bar", action_name="foo")

    assert 0 == dispatcher.get_expiring_action_count()
    assert 1 == dispatcher.get_scheduled_action_count()

    dispatcher.expire_action(
        scheduler_name="bar",
        action_name="foo",
        expire_on=Now.dt() + timedelta(seconds=1),
    )

    assert 1 == dispatcher.get_expiring_action_count()
    assert 1 == dispatcher.get_scheduled_action_count()

    time.sleep(6)  # the out-of-band job runs every 2-5 seconds

    assert 0 == dispatcher.get_expiring_action_count()
    assert 0 == dispatcher.get_scheduled_action_count()


def test_expire_action_action(friends):
    """
    Want to observe the scheduling move from deferred state to ready state.
    """
    dispatcher, scheduler, action = friends()
    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)

    assert 0 == dispatcher.get_expiring_action_count()
    assert 0 == dispatcher.get_scheduled_action_count()

    dispatcher.schedule_action(scheduler_name="bar", action_name="foo")

    assert 0 == dispatcher.get_expiring_action_count()
    assert 1 == dispatcher.get_scheduled_action_count()

    expire_action = ExpireAction(
        scheduler_name="bar",
        action_name="foo",
        expire_on=DateTime(dt=Now.dt() + timedelta(seconds=2)),
    )
    expire_action.execute()

    assert 1 == dispatcher.get_expiring_action_count()
    assert 1 == dispatcher.get_scheduled_action_count()

    time.sleep(6)  # the out-of-band job runs every 2-5 seconds

    assert 0 == dispatcher.get_expiring_action_count()
    assert 0 == dispatcher.get_scheduled_action_count()


def test_immediately(friends):
    """
    Want to observe that action get executed immediately and that schedulers_actions
    is not impacted.
    """

    dispatcher, scheduler, action = friends()

    class TestAction(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result(result=self.fleas)

    test_action = TestAction()

    assert dispatcher.get_scheduled_action_count() == 0
    assert test_action.fleas == 0

    dispatcher.add_action("foo", test_action)
    dispatcher.add_scheduler("imm", Immediately())
    dispatcher.schedule_action(scheduler_name="imm", action_name="foo")

    assert dispatcher.get_scheduled_action_count() == 0
    assert test_action.fleas == 1


def test_program_1(friends):
    """
    Want to observe that a Program's actions are executed.
    """

    dispatcher, scheduler, action = friends()

    class TestAction1(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    class TestAction2(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    class TestAction3(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    action1 = TestAction1()
    action2 = TestAction2()
    action3 = TestAction3()

    dispatcher.add_action("foo1", action1)
    dispatcher.add_action("foo2", action2)
    dispatcher.add_action("foo3", action3)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.add_scheduler("immediately", Immediately())

    program = PBEProgram().prologue("foo1").body_element("bar", "foo2").epilogue("foo3")
    dispatcher.add_program("baz", program)

    start = Now().dt() + timedelta(seconds=1)
    stop = start + timedelta(seconds=4)

    dispatcher.run_jobs()
    dispatcher.schedule_program("baz", start, stop)

    assert action1.fleas == 0
    time.sleep(3)
    assert action1.fleas == 1
    time.sleep(4)
    assert action2.fleas >= 2
    time.sleep(2)
    assert action3.fleas == 1


def test_unschedule_program(friends):
    """
    Want to observe that a Program's actions are not executed
    after being unscheduled prior to the deferral time.
    """

    dispatcher, scheduler, action = friends()

    class TestAction1(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    class TestAction2(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    class TestAction3(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    action1 = TestAction1()
    action2 = TestAction2()
    action3 = TestAction3()

    dispatcher.add_action("foo1", action1)
    dispatcher.add_action("foo2", action2)
    dispatcher.add_action("foo3", action3)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.add_scheduler("immediately", Immediately())

    program = PBEProgram().prologue("foo1").body_element("bar", "foo2").epilogue("foo3")
    dispatcher.add_program("baz", program)
    start = Now().dt() + timedelta(seconds=4)
    stop = start + timedelta(seconds=4)

    dispatcher.run_jobs()
    dispatcher.schedule_program("baz", start, stop)
    assert dispatcher.get_deferred_program_count() == 1
    assert dispatcher.get_scheduled_action_count() == 0

    dispatcher.unschedule_program("baz")
    assert len(dispatcher.get_programs()) == 1
    print("BLEEEEEE", dispatcher.get_deferred_programs())
    assert dispatcher.get_deferred_program_count() == 0

    assert action1.fleas == 0
    time.sleep(3)
    assert action1.fleas == 0
    time.sleep(4)
    assert action2.fleas == 0
    time.sleep(2)
    assert action3.fleas == 0


def test_unschedule_program_action(friends):
    """
    Want to observe that a Program's actions are not executed
    after being unscheduled prior to the deferral time.
    """

    dispatcher, scheduler, action = friends()

    class TestAction1(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    class TestAction2(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    class TestAction3(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    action1 = TestAction1()
    action2 = TestAction2()
    action3 = TestAction3()

    dispatcher.add_action("foo1", action1)
    dispatcher.add_action("foo2", action2)
    dispatcher.add_action("foo3", action3)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.add_scheduler("immediately", Immediately())

    program = PBEProgram().prologue("foo1").body_element("bar", "foo2").epilogue("foo3")
    dispatcher.add_program("baz", program)
    start = Now().dt() + timedelta(seconds=4)
    stop = start + timedelta(seconds=4)

    dispatcher.run_jobs()
    dispatcher.schedule_program("baz", start, stop)
    assert dispatcher.get_deferred_program_count() == 1
    assert dispatcher.get_scheduled_action_count() == 0

    unschedule_program = UnscheduleProgram(program_name="baz")
    unschedule_program.execute()
    time.sleep(1)

    assert len(dispatcher.get_programs()) == 1
    assert dispatcher.get_deferred_program_count() == 0

    assert action1.fleas == 0
    time.sleep(3)
    assert action1.fleas == 0
    time.sleep(4)
    assert action2.fleas == 0
    time.sleep(2)
    assert action3.fleas == 0


def test_delete_program(friends):
    """
    Want to observe that a Program's actions are not executed
    after being deleted prior to the deferral time.
    """

    dispatcher, scheduler, action = friends()

    class TestAction1(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    class TestAction2(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    class TestAction3(Action):
        fleas: int = 0

        def execute(self, tag: str = None, rez: Rez = None):
            self.fleas += 1
            return self.action_result()

    action1 = TestAction1()
    action2 = TestAction2()
    action3 = TestAction3()

    dispatcher.add_action("foo1", action1)
    dispatcher.add_action("foo2", action2)
    dispatcher.add_action("foo3", action3)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.add_scheduler("immediately", Immediately())

    program = PBEProgram().prologue("foo1").body_element("bar", "foo2").epilogue("foo3")
    dispatcher.add_program("baz", program)
    start = Now().dt() + timedelta(seconds=4)
    stop = start + timedelta(seconds=4)
    assert len(dispatcher.get_programs()) == 1

    dispatcher.run_jobs()
    dispatcher.schedule_program("baz", start, stop)
    assert dispatcher.get_deferred_program_count() == 1
    assert dispatcher.get_scheduled_action_count() == 0

    dispatcher.delete_program("baz")
    assert len(dispatcher.get_programs()) == 0
    assert dispatcher.get_deferred_program_count() == 0

    assert action1.fleas == 0
    time.sleep(3)
    assert action1.fleas == 0
    time.sleep(4)
    assert action2.fleas == 0
    time.sleep(2)
    assert action3.fleas == 0


def test_execute_with_rez(friends):
    """
    Want to see execute work with supplied dictionary.
    """
    dispatcher, scheduler, action = friends()
    result = action.execute(rez=Rez(result={"fleacount": "infinite"}))
    assert result.rez.result == {"fleacount": "infinite"}


def test_terminate_scheduler(friends):
    """
    Want to terminate scheduler using TerminateScheduler action.
    """
    dispatcher, scheduler, action = friends()
    action2 = Terminate()
    dispatcher.add_action("foo", action)
    dispatcher.add_action("terminate", action2)
    dispatcher.add_scheduler("bar", scheduler)

    dispatcher.run_jobs()
    dispatcher.schedule_action("bar", "foo")
    time.sleep(2)
    assert action.flea_count >= 1
    assert dispatcher.get_scheduled_action_count() == 1
    dispatcher.schedule_action("bar", "terminate")
    assert dispatcher.get_scheduled_action_count() == 2
    time.sleep(2)
    assert dispatcher.get_scheduled_action_count() == 0


def test_terminate_scheduler_and(friends):
    """
    Want to terminate scheduler using TerminateScheduler action.
    """
    dispatcher, scheduler, action = friends()
    action2 = FleaCount(flea_count=100)
    actions = [action, Terminate(), action2]
    action3 = (
        UntilFailure()
    )  # add actions on next line to use them directly below; pydantic deep copies field values
    action3.actions = actions
    dispatcher.add_action("foo", action3)
    dispatcher.add_scheduler("bar", scheduler)

    dispatcher.run_jobs()
    dispatcher.schedule_action("bar", "foo")
    time.sleep(3)
    assert action.flea_count == 1
    assert action2.flea_count == 100


def test_if_else_1(friends):
    """
    Want to terminate scheduler using TerminateScheduler action.
    """
    dispatcher, scheduler, action = friends()
    action2 = FleaCount(flea_count=100)
    immediately = Immediately()
    dispatcher.add_action("foo1", action)
    dispatcher.add_action("foo2", action2)
    dispatcher.add_scheduler("immediately", immediately)

    if_else = IfElse(
        test_action=RaiseCmp(value=1),
        if_action=ScheduleAction(scheduler_name="immediately", action_name="foo1"),
        else_action=ScheduleAction(scheduler_name="immediately", action_name="foo2"),
    )
    schedule_action = All(actions=[Result(value=2), if_else])

    dispatcher.add_action("schedule_action", schedule_action)
    dispatcher.schedule_action("immediately", "schedule_action")

    assert action.flea_count == 1
    assert action2.flea_count == 100


def test_if_else_2(friends):
    """
    Want to terminate scheduler using TerminateScheduler action.
    """
    dispatcher, scheduler, action = friends()
    action2 = FleaCount(flea_count=100)
    immediately = Immediately()
    dispatcher.add_action("foo1", action)
    dispatcher.add_action("foo2", action2)
    dispatcher.add_scheduler("immediately", immediately)

    if_else = IfElse(
        test_action=RaiseCmp(value=2),
        if_action=ScheduleAction(scheduler_name="immediately", action_name="foo1"),
        else_action=ScheduleAction(scheduler_name="immediately", action_name="foo2"),
    )
    schedule_action = All(actions=[Result(value=2), if_else])

    dispatcher.add_action("schedule_action", schedule_action)
    dispatcher.schedule_action("immediately", "schedule_action")

    assert action.flea_count == 0
    assert action2.flea_count == 101


# ====================================


class FleaCount(Action):
    flea_count: int = 0
    data: Optional[Dict[Any, Any]]

    def execute(self, tag: str = None, rez: Rez = None):
        self.flea_count += 1
        return self.action_result(
            result=self.flea_count, rez=rez, flds=rez.flds if rez else {}
        )


@pytest.fixture
def friends(tmp_path, host, port):
    """ returns a tuple of useful test objects """
    SystemInfo.init(host, port)

    def stuff():
        # want a fresh tuple from the fixture
        dispatcher = Dispatcher(saved_dir=str(tmp_path))
        dispatcher.set_timed(Timed())
        dispatcher.initialize()
        action = FleaCount()
        scheduler = Timely(interval=1)

        return dispatcher, scheduler, action

    return stuff


@pytest.fixture
def servers():
    def stuff():
        server1 = Server(host="localhost", port=8000)
        server1.add_key_tag("foo", "bar")
        server1.add_key_tag("foo", "baz")
        server1.add_key_tag("fleas", "standdown")
        server1.add_key_tag("krimp", "kramp")
        server2 = Server(host="localhost", port=8000)
        server2.add_key_tag("foo", "bar")
        server2.add_key_tag("fleas", "riseup")
        server2.add_key_tag("slip", "slide")
        return (server1, server2)

    return stuff
