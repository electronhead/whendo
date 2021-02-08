import time
from whendo.core.continuous import Continuous
from whendo.core.util import TimeUnit, PP
from whendo.core.action import Action, ActionPayload

def test_timely_callable(tmp_path):
    """
    This test exercises the schedule_timely_callable method.
    """
    class Suite:
        def __init__(self):
            self.content = 'foobarbaz'
            self.file = 'text.txt'
            self.path = tmp_path / self.file
        def callable(self):
            with self.path.open(mode='a') as fid:
                fid.write(self.content)
                fid.write('\n')
        def gather(self):
            result = []
            with self.path.open(mode='r') as fid:
                result.append(fid.readlines())
            return result
        def run(self):
            continuous = Continuous()
            continuous.schedule_timely_callable('tag', self.callable)
            continuous.run_continuously()
            time.sleep(4)
            continuous.stop_running_continuously()
            continuous.clear()
    suite = Suite()
    suite.run()
    accumulated_content = suite.gather()
    assert accumulated_content and len(accumulated_content) > 0

def test_random_callable(tmp_path):
    """
    This test exercises the schedule_timely_callable method.
    """
    class Suite:
        def __init__(self):
            self.content = 'foobarbaz'
            self.file = 'text.txt'
            self.path = tmp_path / self.file
        def callable(self):
            with self.path.open(mode='a') as fid:
                fid.write(self.content)
                fid.write('\n')
        def gather(self):
            result = []
            with self.path.open(mode='r') as fid:
                result.append(fid.readlines())
            return result
        def run(self):
            continuous = Continuous()
            continuous.schedule_random_callable('tag', self.callable, time_unit=TimeUnit.second, low=1, high=3)
            continuous.run_continuously()
            time.sleep(4)
            continuous.stop_running_continuously()
            continuous.clear()
    suite = Suite()
    suite.run()
    accumulated_content = suite.gather()
    assert accumulated_content and len(accumulated_content) > 0
    
def test_file_action(tmp_path):
    """
    This test exercises the schedule_timely_callable method.
    """

    class FileAction(Action):
        def execute(self, tag=None, scheduler_info:dict=None):
            path = tmp_path / 'test.txt'
            with path.open(mode='a') as fid:
                fid.write('blee\n')
            return {'outcome':'file appended'}

    class Suite():
        def __init__(self, action):
            self.action = action
        def gather(self):
            path = tmp_path / 'test.txt'
            with path.open(mode='r') as fid:
                return sum(1 for line in fid)
        def run(self):
            continuous = Continuous()
            continuous.schedule_timely_callable('tag', self.action.execute)
            continuous.run_continuously()
            time.sleep(4)
            continuous.stop_running_continuously()
            continuous.clear()
    suite = Suite(FileAction())
    suite.run()
    line_count = suite.gather()
    assert line_count and line_count >= 2, "no lines written to file"
    
