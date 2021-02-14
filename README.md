# whendo

What it is -- written in Python, a single process/local file system-based action scheduling API server. No SQL and no No SQL. An action can be something as simple as turning on a raspberry pi pin or blowing a fog horn or capturing scheduled data feeds from a public api.

##What it does:



##To do:

- installation instructions
- pip install whendo (currently a wheel file)
- always more unit tests
- documentation
- later
  - Docker
  - authentication / authorization

##Dependencies [from setup.py]

- install_requires=["uvicorn", "fastapi", "pydantic", "schedule", "requests", "netifaces", "Mock.GPIO"], # includes RPi.GPIO for raspberry pi's
- setup_requires=["pytest-runner"],
- tests_require=["pytest", "httpx", "pytest-asyncio", "asyncio"]

##Running on (so far):

- 32-bit Raspbian Pi OS [pi 4]
- 64-bit Intel-based Mac OS

##Depending on:

- Jupyter Lab notebooks for a lot of stuff
