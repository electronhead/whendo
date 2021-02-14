from datetime import time
import whendo.core.scheduler as sched
from whendo.core.util import Now
from whendo.core.action import Action
    
def test_during_period():

    daytime = (time(6,0,0), time(18,0,0))
    nighttime = (time(18,0,0), time(6,0,0))

    s_daytime = sched.Scheduler(start = daytime[0], stop = daytime[1])
    s_nighttime = sched.Scheduler(start = nighttime[0], stop = nighttime[1])

    class TestAction(Action):
        fleas:int

        def execute(tag:str, scheduler_info:dict):
            return True
    
    action = TestAction(fleas=185000000)

    daytime_callable = s_daytime.during_period(tag='abc', action=action)
    nighttime_callable = s_nighttime.during_period(tag='abc', action=action)

    now = Now.t()

    is_daytime = daytime[0] < now and now < daytime[1]
    if is_daytime:
        assert daytime_callable() and nighttime_callable() is sched.DoNothing.result
    else:
        assert daytime_callable() is sched.DoNothing.result and nighttime_callable()

