from datetime import time
import whendo.core.scheduler as sched
from whendo.core.util import Now
from whendo.core.action import Action
from whendo.core.continuous import Continuous
from .fixtures import friends


def test_during_period():

    daytime = (time(6, 0, 0), time(18, 0, 0))
    nighttime = (time(18, 0, 0), time(6, 0, 0))

    s_daytime = sched.Scheduler(start=daytime[0], stop=daytime[1])
    s_nighttime = sched.Scheduler(start=nighttime[0], stop=nighttime[1])

    class TestAction(Action):
        fleas: int

        def execute(self, tag: str = None, scheduler_info: dict = None):
            return True

    action = TestAction(fleas=185000000)

    daytime_callable = s_daytime.during_period(tag="abc", action=action)
    nighttime_callable = s_nighttime.during_period(tag="abc", action=action)

    now = Now.t()

    is_daytime = daytime[0] < now and now < daytime[1]
    if is_daytime:
        assert daytime_callable() and nighttime_callable() is sched.DoNothing.result
    else:
        assert daytime_callable() is sched.DoNothing.result and nighttime_callable()

def test_wrap():
    """
    Want to observe that the action's execute method was invoked.
    """
    class TestScheduler(sched.Scheduler):
        def schedule_action(self, tag: str, action: Action, continuous:Continuous=Continuous()):
            wrapped_callable = self.wrap(
                thunk=lambda: action.execute(tag=tag, scheduler_info=self.info()),
                tag=tag,
                action_json=action.json(),
                scheduler_json=self.json())
            wrapped_callable()
    
    class TestAction(Action):
        fleas: int = 0
        def execute(self, tag: str = None, scheduler_info: dict = None):
            self.fleas += 1
    
    scheduler = TestScheduler()
    test_action = TestAction()

    assert test_action.fleas == 0
    scheduler.schedule_action(tag="blee", action=test_action)
    assert test_action.fleas == 1


