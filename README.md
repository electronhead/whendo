# whendo

_[A work in progress]_

What it is -- written in Python, a single process/local file system-based action scheduling API server. No SQL and no No SQL. An action can be something as simple as turning on a raspberry pi pin or blowing a fog horn or capturing scheduled data feeds from a public api.

To do:

- factoring of generic scheduling from specific action applications
  - whendo will have a deployment option of a library which is installed via pip by way of a file system
    - pip install /path/to/wheel/file
    - eventually whendo could find its way into pypi.org
  - a goal: relatively seemless linking between whendo and application-specific action suites 
    - the electronhead/alfalfa repository is a first cut at such a linking
    - library dependencies can now be suite-specific
      - this allows support for raspberry pi applications, which require gpio libraries that are not available on other platforms, and other applications running on linux, mac and windows machines.
- logging
- Docker
- authentication / authorization
- more unit tests
- documentation

Relies on (so far):

- Python (3.9.0)
- FastAPI + Uvicorn
- Pydantic
- schedule
- pytest
- httpx
- asyncio

Running on (so far):

- 32-bit Raspbian Pi OS
- 64-bit Intel-based Mac OS

Depending on:

- Jupyter Lab notebooks for a lot of stuff
