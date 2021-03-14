# whendo (When? Do!)

whendo a single process/local file system-based action scheduling API server. No SQL and no No SQL. An action can be something as simple as turning on a raspberry pi pin or blowing a fog horn or capturing scheduled data feeds from a public api.

whendo let's you define actions, test them individually, and schedule them to be performed at specified times and intervals during the day (with schedulers). You can create actions and run schedulers from a python script, within a Python CLI interpreter, within a Jupyter notebook -- basically anywhere you can run Python.

## Dependencies

- install_requires =
    uvicorn >= 0.13.3
    fastapi >= 0.63.0
    pydantic >= 1.7.3
    schedule >= 1.0.0
    requests >= 2.25.1

## Computers tested (so far):

- 32-bit Raspbian Pi OS [pi 3B+, pi 4B]
- 64-bit Intel-based Mac OS
