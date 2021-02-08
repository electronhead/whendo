from datetime import time
from mothership.scheduler import Scheduler
from mothership.util import Now
    
def test_during_period():

    daytime = (time(6,0,0), time(18,0,0))
    nighttime = (time(18,0,0), time(6,0,0))

    s_daytime = Scheduler(start = daytime[0], stop = daytime[1])
    s_nighttime = Scheduler(start = nighttime[0], stop = nighttime[1])

    callable = lambda tag, scheduler_info: True
    daytime_callable = s_daytime.during_period(callable, tag='abc')
    nighttime_callable = s_nighttime.during_period(callable, tag='abc')

    now = Now.t()

    is_daytime = daytime[0] < now and now < daytime[1]
    if is_daytime:
        assert daytime_callable() and not nighttime_callable()
    else:
        assert not daytime_callable() and nighttime_callable()

