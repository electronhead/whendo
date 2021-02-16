# whendo (When? Do!)

whendo a single process/local file system-based action scheduling API server. No SQL and no No SQL. An action can be something as simple as turning on a raspberry pi pin or blowing a fog horn or capturing scheduled data feeds from a public api.

whendo let's you define actions, perform them individually, and schedule them to be performed at specified times and intervals during the day (with schedulers). You can create actions and run schedulers from a python script, within a Python CLI interpreter, within a Jupyter notebook -- basically anywhere you can run Python.

To start a whendo server, in a virtual environment install the wheel file using pip and invoke the run file with Python.
```
(venv) blah blah $ pip install /path/to/wheel/file/
(venv) blah blah $ python run.py --host 127.0.0.1 --port 8000
```
whendo stores its files in {home}/.whendo.
```
from datetime import time
from whendo.sdk.client import Client
from whendo.core.scheduler import TimelyScheduler, RandomlyScheduler
from whendo.core.actions.gpio_action import TogglePin

# create action that toggles pin 25 (connected to red LED)
red_action = TogglePin(pin:25)
# create action that toggles pin 27 (connected to green LED)
green_action = TogglePin(pin:25)

# see how they toggle
[ lambda y: (red_action.execute(), green_action.execute(), time.sleep(y))(x) for x in [1,2,3,4,3,2,1,2,3,4,3,2,1]]

# create a scheduler that executes an action every second
# second after the top of the minute, from 6:00 to 23:00.
# The start and stop times operate on a 24 hour clock.
timely_secondly = TimelyScheduler(interval=1, start=time(6,0,0), stop=time(23,0,0))

randomly_secondly = RandomlyScheduler(interval=1, start=time(6,0,0), stop=time(23,0,0))

# scheduled run...
client = Client(host='127.0.0.1', port=8000)
client.add_action('green_action', green_action)
client.add_action('red_action', red_action)
client.add_scheduler('timely_secondly', timely_secondly)
client.add_scheduler('randomly_secondly', randomly_secondly)
client.schedule_action('timely_secondly', 'green_action')
client.schedule_action('randomly_secondly', 'red_action')
client.run_jobs()

# change to pin 27
red_toggle.pin = 27

# since red_toggle is already scheduled, the system automatically
#reschedules the action after setting to the new value.
client.set_action('red_toggle', red_toggle)

# run individually through the client
client.execute_action('red_toggle')

client.stop_jobs()
```
## Dependencies [from setup.py]

- install_requires=["uvicorn", "fastapi", "pydantic", "schedule", "requests", "netifaces", "Mock.GPIO"], # includes RPi.GPIO for raspberry pi's
- setup_requires=["pytest-runner"],
- tests_require=["pytest", "httpx", "pytest-asyncio", "asyncio"]

## Computers tested (so far):

- 32-bit Raspbian Pi OS [pi 4]
- 64-bit Intel-based Mac OS
