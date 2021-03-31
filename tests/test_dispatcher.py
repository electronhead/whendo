import pytest
import time
from datetime import timedelta
import whendo.core.util as util
from typing import Optional, Dict, Any
from whendo.core.action import Action
from whendo.core.schedulers.timed_scheduler import Timely
from whendo.core.scheduler import Immediately
from whendo.core.dispatcher import Dispatcher
from whendo.core.programs.simple_program import PBEProgram
from whendo.core.timed import Timed

pause = 3


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
    assert {"bath"} == set(k for k in dispatcher.get_scheduled_actions())
    assert {"flea"} == set(dispatcher.get_scheduled_actions()["bath"])


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
    assert set(k for k in dispatcher.get_scheduled_actions()) == set(
        k for k in dispatcher2.get_scheduled_actions()
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
        scheduler_name="bar", action_name="foo", wait_until=util.Now.dt()
    )

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
        expire_on=util.Now.dt() + timedelta(seconds=1),
    )

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

        def execute(self, tag: str = None, data: dict = None):
            self.fleas += 1
            return "BLING"

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

        def execute(self, tag: str = None, data: dict = None):
            self.fleas += 1
            return "BLING"

    class TestAction2(Action):
        fleas: int = 0

        def execute(self, tag: str = None, data: dict = None):
            self.fleas += 1
            return "BLING"

    class TestAction3(Action):
        fleas: int = 0

        def execute(self, tag: str = None, data: dict = None):
            self.fleas += 1
            return "BLING"

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
    start = util.Now().dt() + timedelta(seconds=1)
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

        def execute(self, tag: str = None, data: dict = None):
            self.fleas += 1
            return "BLING"

    class TestAction2(Action):
        fleas: int = 0

        def execute(self, tag: str = None, data: dict = None):
            self.fleas += 1
            return "BLING"

    class TestAction3(Action):
        fleas: int = 0

        def execute(self, tag: str = None, data: dict = None):
            self.fleas += 1
            return "BLING"

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
    start = util.Now().dt() + timedelta(seconds=4)
    stop = start + timedelta(seconds=4)

    dispatcher.run_jobs()
    dispatcher.schedule_program("baz", start, stop)
    assert dispatcher.get_deferred_program_count() == 1
    assert dispatcher.get_scheduled_action_count() == 0

    dispatcher.unschedule_program("baz")
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

        def execute(self, tag: str = None, data: dict = None):
            self.fleas += 1
            return "BLING"

    class TestAction2(Action):
        fleas: int = 0

        def execute(self, tag: str = None, data: dict = None):
            self.fleas += 1
            return "BLING"

    class TestAction3(Action):
        fleas: int = 0

        def execute(self, tag: str = None, data: dict = None):
            self.fleas += 1
            return "BLING"

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
    start = util.Now().dt() + timedelta(seconds=4)
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


def test_execute_with_data(friends):
    """
    Want to see execute work with supplied dictionary.
    """
    dispatcher, scheduler, action = friends()
    action.execute(data={"fleacount": "infinite"})
    assert action.data == {"fleacount": "infinite"}


@pytest.fixture
def friends(tmp_path):
    """ returns a tuple of useful test objects """

    class FleaCount(Action):
        flea_count: int = 0
        data: Optional[Dict[Any, Any]]

        def execute(self, tag: str = None, data: dict = None):
            self.flea_count += 1
            self.data = data

    def stuff():
        # want a fresh tuple from the fixture
        dispatcher = Dispatcher(saved_dir=str(tmp_path))
        dispatcher.set_timed(Timed())
        dispatcher.initialize()
        action = FleaCount()
        scheduler = Timely(interval=1)

        return dispatcher, scheduler, action

    return stuff
