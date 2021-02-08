# pyrambium

_[A work in progress]_

What it is -- written in Python, a single process/local file system-based action scheduling API server. No SQL and no No SQL. An action can be something as simple as turning on a raspberry pi pin or blowing a fog horn.

To do:

- logging
- Docker
- authentication / authorization
- Nginx coupling
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
