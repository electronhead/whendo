import pytest
import time
from whendo.core.dispatcher import Dispatcher
from test.fixtures import friends

def test_schedule_action(friends):
    """
    Tests Dispatcher and Continuous objects running a scheduled action.
    """
    dispatcher, scheduler, action = friends()

    dispatcher.add_action('foo', action)
    dispatcher.add_scheduler('bar', scheduler)
    dispatcher.schedule_action('bar', 'foo')

    continuous = dispatcher.get_continuous()
    continuous.run_continuously()
    time.sleep(4)
    continuous.stop_running_continuously()
    continuous.clear()

    line = None
    with open(action.file, 'r') as fid:
        line = fid.readline()
    assert line is not None and type(line) is str and len(line) > 0

def test_unschedule_action(friends):
    """
    Tests unscheduling an action.
    """
    dispatcher, scheduler, action = friends()

    dispatcher.add_action('foo', action)
    dispatcher.add_scheduler('bar', scheduler)
    dispatcher.schedule_action('bar', 'foo')
    dispatcher.unschedule_action('foo')

    continuous = dispatcher.get_continuous()
    assert continuous.job_count() == 0
    assert dispatcher.get_scheduled_action_count() == continuous.job_count()

def test_reschedule_action(friends):
    """
    Tests unscheduling and then rescheduling an action.
    """
    dispatcher, scheduler, action = friends()
    continuous = dispatcher.get_continuous()
    assert continuous.job_count() == 0

    dispatcher.add_action('foo', action)
    dispatcher.add_scheduler('bar', scheduler)
    dispatcher.schedule_action('bar', 'foo')
    dispatcher.reschedule_action('foo')

    continuous.run_continuously()
    time.sleep(4)
    continuous.stop_running_continuously()
    continuous.clear()

    line = None
    with open(action.file, 'r') as fid:
        line = fid.readline()

    assert line is not None and type(line) is str and len(line) > 0

def test_reschedule_action_2(friends, tmp_path):
    """
    Tests unscheduling and then rescheduling an action.
    """
    dispatcher, scheduler, action = friends()
    continuous = dispatcher.get_continuous()
    assert continuous.job_count() == 0

    dispatcher.add_action('foo', action)
    dispatcher.add_scheduler('bar', scheduler)
    dispatcher.schedule_action('bar', 'foo')
    stored_action = dispatcher.get_action('foo')
    stored_action.file = str(tmp_path / 'output2.txt')
    dispatcher.set_action('foo', stored_action)
    dispatcher.reschedule_action('foo')

    continuous.run_continuously()
    time.sleep(4)
    continuous.stop_running_continuously()
    continuous.clear()

    line = None
    with open(stored_action.file, 'r') as fid:
        line = fid.readline()
    assert line is not None and type(line) is str and len(line) > 0

def test_unschedule_scheduler(friends):
    """
    Tests unscheduling a scheduler.
    """
    dispatcher, scheduler, action = friends()
    continuous = dispatcher.get_continuous()
    assert continuous.job_count() == 0

    dispatcher.add_action('foo', action)
    dispatcher.add_scheduler('bar', scheduler)
    dispatcher.schedule_action('bar', 'foo')
    
    assert continuous.job_count() == 1

    dispatcher.unschedule_scheduler('bar')

    assert continuous.job_count() == 0
    assert dispatcher.get_scheduled_action_count() == continuous.job_count()

    # make sure that bar and foo remain
    assert dispatcher.get_scheduler('bar')
    assert dispatcher.get_action('foo')


def test_clear_dispatcher(friends):
    """
    Tests clearing a dispatcher.
    """
    dispatcher, scheduler, action = friends()
    continuous = dispatcher.get_continuous()
    assert continuous.job_count() == 0

    dispatcher.add_action('foo', action)
    dispatcher.add_scheduler('bar', scheduler)
    dispatcher.schedule_action('bar', 'foo')
    assert continuous.job_count() == 1
    
    dispatcher.clear_all()
    assert continuous.job_count() == 0
    assert dispatcher.get_scheduled_action_count() == continuous.job_count()

    # make sure that bar and foo are Gone
    assert dispatcher.get_scheduler('bar') is None
    assert dispatcher.get_action('foo') is None

def test_saved_dir_1(tmp_path):
    saved_dir = str(tmp_path)
    dispatcher = Dispatcher()
    dispatcher.set_saved_dir(saved_dir=saved_dir)
    assert dispatcher.get_saved_dir() == saved_dir

def test_saved_dir_2(tmp_path):
    saved_dir = str(tmp_path)
    dispatcher = Dispatcher(saved_dir=saved_dir)
    assert dispatcher.get_saved_dir() == saved_dir