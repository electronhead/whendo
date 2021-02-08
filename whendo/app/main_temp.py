"""
This module is the top of the path tree. Establishes all sub-path routers.

It is used for unit testing.
"""
from fastapi import FastAPI
from mothership.mothership import Mothership
from mothership.continuous import Continuous
from app.router import actions, schedulers, mothership, jobs
from app.shared import set_continuous, set_mothership

app = FastAPI()

@app.get('/')
async def root():
    return 'Pyrambium API server started (unit test)'

mothership_instance = Mothership()
continuous_instance = Continuous()
mothership_instance.set_continuous(continuous_instance)

app.include_router(set_mothership(actions.router, mothership_instance))
app.include_router(set_mothership(schedulers.router, mothership_instance))
app.include_router(set_mothership(mothership.router, mothership_instance))
app.include_router(set_continuous(jobs.router, continuous_instance))