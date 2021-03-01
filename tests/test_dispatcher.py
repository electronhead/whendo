import pytest
import time
import json
import datetime
import whendo.core.util as util
from whendo.core.action import Action
from whendo.core.scheduler import Immediately
from whendo.core.dispatcher import Dispatcher
from .fixtures import friends

pause = 2


def test_schedule_action(friends):
    """
    Tests Dispatcher and Continuous objects running a scheduled action.
    """
    dispatcher, scheduler, action = friends()

    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action("bar", "foo")

    dispatcher.run_jobs()
    time.sleep(pause)
    dispatcher.stop_jobs()
    dispatcher.clear_jobs()

    line = None
    with open(action.file, "r") as fid:
        line = fid.readline()
    assert line is not None and type(line) is str and len(line) > 0


def test_unschedule_action(friends):
    """
    Tests unscheduling an action.
    """
    dispatcher, scheduler, action = friends()

    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action("bar", "foo")
    assert dispatcher.job_count() == 1
    dispatcher.unschedule_action("foo")
    assert dispatcher.job_count() == 0
    assert dispatcher.get_scheduled_action_count() == dispatcher.job_count()


def test_reschedule_action(friends):
    """
    Tests unscheduling and then rescheduling an action.
    """
    dispatcher, scheduler, action = friends()
    assert dispatcher.job_count() == 0

    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action("bar", "foo")
    dispatcher.reschedule_action("foo")

    dispatcher.run_jobs()
    time.sleep(pause)
    dispatcher.stop_jobs()
    dispatcher.clear_jobs()

    line = None
    with open(action.file, "r") as fid:
        line = fid.readline()

    assert line is not None and type(line) is str and len(line) > 0


def test_reschedule_action_2(friends, tmp_path):
    """
    Tests unscheduling and then rescheduling an action.
    """
    dispatcher, scheduler, action = friends()
    assert dispatcher.job_count() == 0

    dispatcher.add_action("foo", action)
    dispatcher.add_scheduler("bar", scheduler)
    dispatcher.schedule_action("bar", "foo")
    stored_action = dispatcher.get_action("foo")
    stored_action.file = str(tmp_path / "output2.txt")
    dispatcher.set_action("foo", stored_action)
    dispatcher.reschedule_action("foo")

    dispatcher.run_jobs()
    time.sleep(pause)
    dispatcher.stop_jobs()
    dispatcher.clear_jobs()

    line = None
    with open(stored_action.file, "r") as fid:
        line = fid.readline()
    assert line is not None and type(line) is str and len(line) > 0


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

    dispatcher.clear_jobs()
    assert dispatcher.job_count() == 0

    dispatcher.add_action("foo2", action)
    dispatcher.schedule_action("bar", "foo2")
    assert dispatcher.job_count() == 1

    dispatcher.reschedule_all_schedulers()
    assert dispatcher.job_count() == 2

    assert dispatcher.get_scheduled_action_count() == dispatcher.job_count()


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
    assert {"bath"} == set(k for k in dispatcher.get_schedulers_actions())
    assert {"flea"} == set(dispatcher.get_schedulers_actions()["bath"])


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
    assert set(k for k in dispatcher.get_schedulers_actions()) == set(
        k for k in dispatcher2.get_schedulers_actions()
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

    assert 0 == dispatcher.get_expired_action_count()
    assert 0 == dispatcher.get_scheduled_action_count()

    dispatcher.schedule_action(scheduler_name="bar", action_name="foo")

    assert 0 == dispatcher.get_expired_action_count()
    assert 1 == dispatcher.get_scheduled_action_count()

    dispatcher.expire_action(
        scheduler_name="bar", action_name="foo", expire_on=util.Now.dt() + datetime.timedelta(seconds=1)
    )

    assert 1 == dispatcher.get_expired_action_count()
    assert 1 == dispatcher.get_scheduled_action_count()

    time.sleep(6)  # the out-of-band job runs every 2-5 seconds

    assert 0 == dispatcher.get_expired_action_count()
    assert 0 == dispatcher.get_scheduled_action_count()



def test_immediately(friends):
    """
    Want to observe that action get executed immediately and that schedulers_actions
    is not impacted.
    """

    dispatcher, scheduler, action = friends()

    class TestAction(Action):
        fleas: int = 0

        def execute(self, tag: str = None, scheduler_info: dict = None):
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