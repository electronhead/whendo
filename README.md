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
from whendo.core.scheduler import TimelyScheduler
from whendo.core.actions.gpio_action import TogglePin

# create an action that toggles pin 25 (connected to red LED)
red_action = TogglePin(pin:25)

# create a scheduler that executes an action at the 15th
# second after the top of the minute, from 8:00 to 18:00.
# The start and stop times operate on a 24 hour clock.
daily_by_minute = TimelyScheduler(interval=1, start=time(8,0,0), stop=time(18,0,0))
# reverse the start and stop times to start at 18:00 and stop
# at 8:00.
nightly_by_minute = TimelyScheduler(interval=1, start=time(18,0,0), stop=time(8,0,0))

# run individually...
red_action.execute()
# or directly...
TogglePin(pin:25).execute()

# scheduled run...
client = Client(host='127.0.0.1', port=8000)
client.add_action('red_toggle', red_action)
client.add_scheduler('daily_by_minute', daily_by_minute)
client.schedule_action('hourly_daily', 'red_toggle')
client.start_jobs()

# change to pin 27
red_toggle.pin = 27

# since red_toggle is already scheduled, the system automatically
#reschedules the action after setting to the new value.
client.set_action('red_toggle', red_toggle)

# run individually through the client
client.execute_action('red_toggle')

client.stop_jobs()
```

## To do:

- installation instructions
- pip install whendo (currently a wheel file)
- always more unit tests
- documentation
- later
  - Docker
  - authentication / authorization

## Dependencies [from setup.py]

- install_requires=["uvicorn", "fastapi", "pydantic", "schedule", "requests", "netifaces", "Mock.GPIO"], # includes RPi.GPIO for raspberry pi's
- setup_requires=["pytest-runner"],
- tests_require=["pytest", "httpx", "pytest-asyncio", "asyncio"]

## Computers tested (so far):

- 32-bit Raspbian Pi OS [pi 4]
- 64-bit Intel-based Mac OS
