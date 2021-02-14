# whendo

What it is -- written in Python, a single process/local file system-based action scheduling API server. No SQL and no No SQL. An action can be something as simple as turning on a raspberry pi pin or blowing a fog horn or capturing scheduled data feeds from a public api.

## What it does:

whendo let's you define actions, perform them individually, and schedule them to be performed at specified times and intervals during the day (with schedulers). You can create actions and run schedulers from a python script, within a Python CLI interpreter, within a Jupyter notebook -- basically anywhere you can run Python.

```
from whendo.sdk.client import Client

red_action = TogglePin(pin:25)
daily_by_minute = TimelyScheduler(interval=1, start=time(8,0,0), stop=time(18,0,0), second=15)

# run individually
red_action.execute()

# scheduled run -- 
client = Client(ip_addr='127.0.0.1', port=8000)
client.add_action('red_toggle', red_action)
client.add_scheduler('daily_by_minute', daily_by_minute)
client.schedule_action('hourly_daily', 'red_toggle')
client.start_jobs()
# change to pin 27
red_toggle.pin = 27
client.unschedule_action('red_toggle')
client.set_action('red_toggle', red_toggle)
client.schedule_action('daily_by_minute', 'red_toggle')
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
