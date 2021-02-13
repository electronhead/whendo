import pytest
import time
from whendo.core.mothership import Mothership
from test.fixtures import friends

def test_schedule_action(friends):
    """
    Tests Mothership and Continuous objects running a scheduled action.
    """
    mothership, scheduler, action = friends()

    mothership.add_action('foo', action)
    mothership.add_scheduler('bar', scheduler)
    mothership.schedule_action('bar', 'foo')

    continuous = mothership.get_continuous()
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
    mothership, scheduler, action = friends()

    mothership.add_action('foo', action)
    mothership.add_scheduler('bar', scheduler)
    mothership.schedule_action('bar', 'foo')
    mothership.unschedule_action('foo')

    continuous = mothership.get_continuous()
    assert continuous.job_count() == 0
    assert mothership.get_scheduled_action_count() == continuous.job_count()

def test_reschedule_action(friends):
    """
    Tests unscheduling and then rescheduling an action.
    """
    mothership, scheduler, action = friends()
    continuous = mothership.get_continuous()
    assert continuous.job_count() == 0

    mothership.add_action('foo', action)
    mothership.add_scheduler('bar', scheduler)
    mothership.schedule_action('bar', 'foo')
    mothership.unschedule_action('foo')
    mothership.schedule_action('bar', 'foo')

    continuous.run_continuously()
    time.sleep(4)
    continuous.stop_running_continuously()
    continuous.clear()

    line = None
    with open(action.file, 'r') as fid:
        line = fid.readline()

    assert line is not None and type(line) is str and len(line) > 0

def test_unschedule_scheduler(friends):
    """
    Tests unscheduling a scheduler.
    """
    mothership, scheduler, action = friends()
    continuous = mothership.get_continuous()
    assert continuous.job_count() == 0

    mothership.add_action('foo', action)
    mothership.add_scheduler('bar', scheduler)
    mothership.schedule_action('bar', 'foo')
    
    assert continuous.job_count() == 1

    mothership.unschedule_scheduler('bar')

    assert continuous.job_count() == 0
    assert mothership.get_scheduled_action_count() == continuous.job_count()

    # make sure that bar and foo remain
    assert mothership.get_scheduler('bar')
    assert mothership.get_action('foo')

def test_saved_dir_1(tmp_path):
    saved_dir = str(tmp_path)
    mothership = Mothership()
    mothership.set_saved_dir(saved_dir=saved_dir)
    assert mothership.get_saved_dir() == saved_dir

def test_saved_dir_2(tmp_path):
    saved_dir = str(tmp_path)
    mothership = Mothership(saved_dir=saved_dir)
    assert mothership.get_saved_dir() == saved_dir