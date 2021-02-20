from datetime import time
from whendo.sdk.client import Client
from whendo.sdk.workbench import Workbench
from whendo.core.util import IP, PP, FilePathe, Dirs, TimeUnit
import whendo.core.actions.file_action as file_x
import whendo.core.actions.logic_action as logic_x
import whendo.core.scheduler as sched_x
import whendo.core.actions.gpio_action as gpio_x

workbench = Workbench()
workbench.add_client("local", Client(host=IP.local))
workbench.add_client("pi", Client(host="192.168.0.45"))
local = workbench.get_client("local")
pi = workbench.get_client("pi")
output_dir = Dirs.output_dir()

client = local

client.clear_dispatcher()

"""
define the actions
"""
green_on = gpio_x.SetPin(pin=27, on=True)
green_off = gpio_x.SetPin(pin=27, on=True)
green_toggle = gpio_x.TogglePin(pin=27)
red_on = gpio_x.SetPin(pin=25, on=True)
red_off = gpio_x.SetPin(pin=25, on=True)
red_toggle = gpio_x.TogglePin(pin=25)
gpio_clear = gpio_x.Cleanup(cleanup="cleanup")
toggle_toggle = logic_x.ListAction(
    op_mode=logic_x.ListOpMode.ALL, action_list=[green_toggle, red_toggle]
)
file_heartbeat = file_x.FileHeartbeat(file=f"{output_dir}gpio_beat.txt")

"""
define the schedulers
"""
morning, evening = time(6, 0, 0), time(18, 0, 0)
daily_often = sched_x.TimelyScheduler(start=morning, stop=evening, interval=1)
nightly_often = sched_x.TimelyScheduler(start=evening, stop=morning, interval=1)
randomly_often = sched_x.RandomlyScheduler(time_unit=TimeUnit.second, low=2, high=5)
timely_at_00_sec = sched_x.TimelyScheduler(interval=1, second=00)
timely_at_30_sec = sched_x.TimelyScheduler(interval=1, second=30)

"""
add actions to the 'client' dispatcher
"""
[
    client.add_action(*action)
    for action in [
        ("green_on", green_on),
        ("green_off", green_off),
        ("green_toggle", green_toggle),
        ("red_on", red_on),
        ("red_off", red_off),
        ("red_toggle", red_toggle),
        ("gpio_clear", gpio_clear),
        ("toggle_toggle", toggle_toggle),
        ("file_heartbeat", file_heartbeat),
    ]
]

"""
add schedulers to the 'client' dispatcher
"""
[
    client.add_scheduler(*scheduler)
    for scheduler in [
        ("daily_often", daily_often),
        ("nightly_often", nightly_often),
        ("randomly_often", randomly_often),
        ("timely_at_00_sec", timely_at_00_sec),
        ("timely_at_30_sec", timely_at_30_sec),
    ]
]

"""
schedule the actions of interest
"""
[
    client.schedule_action(*stuff)
    for stuff in [
        ("randomly_often", "red_toggle"),
        ("daily_often", "green_toggle"),
        ("nightly_often", "green_toggle")
        # ('nightly_often', 'toggle_toggle')
        # ('randomly_often', 'file_heartbeat')
    ]
]
