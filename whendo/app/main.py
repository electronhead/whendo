"""
This module is the top of the path tree. Establishes all sub-path routers.

It is used for command line invocation.
"""
from fastapi import FastAPI
from mothership.mothership import MothershipsLittleHelper
from mothership.continuous import Continuous
from app.router import actions, schedulers, mothership, jobs
from app.shared import set_continuous, set_mothership

app = FastAPI()

@app.get('/')
async def root():
    return 'Pyrambium API server started'

mothership_instance = MothershipsLittleHelper.get()
continuous_instance = mothership_instance.get_continuous()

app.include_router(set_mothership(actions.router, mothership_instance))
app.include_router(set_mothership(schedulers.router, mothership_instance))
app.include_router(set_mothership(mothership.router, mothership_instance))
app.include_router(set_continuous(jobs.router, continuous_instance))