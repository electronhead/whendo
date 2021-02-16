# whendo (When? Do!)

whendo a single process/local file system-based action scheduling API server. No SQL and no No SQL. An action can be something as simple as turning on a raspberry pi pin or blowing a fog horn or capturing scheduled data feeds from a public api.

whendo let's you define actions, test them individually, and schedule them to be performed at specified times and intervals during the day (with schedulers). You can create actions and run schedulers from a python script, within a Python CLI interpreter, within a Jupyter notebook -- basically anywhere you can run Python.

To start a whendo server, in a virtual environment install the wheel file using pip and invoke the run file with Python.
```
(venv) blah blah $ pip install /path/to/wheel/file/
(venv) blah blah $ python run.py --host 127.0.0.1 --port 8000
```
whendo stores its files in {home}/.whendo. What follows in a script that illustrates interacting with a remote whendo server that has pin 27 connected to a green LED and pin 25 connected to a red LED. This script was developed in a Jupyter notebook in VSCode running on a pi 4.
```
from datetime import time
import time as thyme
from whendo.sdk.client import Client
from whendo.core.scheduler import TimelyScheduler, RandomlyScheduler
from whendo.core.actions.gpio_action import TogglePin, SetPin, Cleanup
from whendo.core.util import TimeUnit

# create action that toggles pin 25 (connected to red LED)
red_toggle = TogglePin(pin=25)
red_off = SetPin(pin=red_toggle.pin, on=False)
# create action that toggles pin 27 (connected to green LED)
green_toggle = TogglePin(pin=27)
green_off = SetPin(pin=green_toggle.pin, on=False)

gpio_cleanup = Cleanup()

# create schedulers that executes an action every second from 18:00 to 8:00.
# Start/stop specify intervals 24 hours or less. The random one executes
# randomly from a period 2 to 5 seconds from the previous execution.
timely_secondly = TimelyScheduler(interval=1, start=time(18,0,0), stop=time(8,0,0))
randomly_secondly = RandomlyScheduler(interval=1, start=time(18,0,0), stop=time(6,0,0), low=2, high=5, time_unit=TimeUnit.second)

# SDK
# A client could be any reachable pi with whendo running on it
# with the same action libraries. Use a Jupyter notebook
# to interact with a fleet of pi's.
client = Client(host='127.0.0.1', port=8000)
client.clear_dispatcher() # deletes all actions and schedulers

client.add_action('red_toggle', red_toggle)
client.add_action('green_toggle', green_toggle)

client.add_scheduler('timely_secondly', timely_secondly)
client.add_scheduler('randomly_secondly', randomly_secondly)

client.schedule_action('timely_secondly', 'green_toggle')
client.schedule_action('randomly_secondly', 'red_toggle')

client.add_action('red_off', red_off)
client.add_action('green_off', green_off)
client.add_action('gpio_cleanup', gpio_cleanup)

client.run_jobs()
thyme.sleep(20)
client.stop_jobs()

# make sure the pins are turned off and GPIO cleaned up
client.execute_action('green_off')
client.execute_action('red_off')
client.execute_action('gpio_cleanup')
```
## Dependencies [from setup.py]

- install_requires=["uvicorn", "fastapi", "pydantic", "schedule", "requests", "netifaces", "Mock.GPIO"], # includes RPi.GPIO for raspberry pi's
- setup_requires=["pytest-runner"],
- tests_require=["pytest", "httpx", "pytest-asyncio", "asyncio"]

## Computers tested (so far):

- 32-bit Raspbian Pi OS [pi 4]
- 64-bit Intel-based Mac OS
