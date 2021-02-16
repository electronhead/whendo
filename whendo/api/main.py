"""
This module is the top of the path tree. Establishes all sub-path routers.

It is used for command line invocation.
"""
from fastapi import FastAPI
from whendo.core.dispatcher import DispatcherSingleton
from whendo.core.continuous import Continuous
from whendo.api.router import actions, schedulers, dispatcher, jobs
from whendo.api.shared import set_dispatcher
import whendo.log.init

app = FastAPI()

@app.get('/')
async def root():
    return 'whengo API server started'

dispatcher_instance = DispatcherSingleton.get()

app.include_router(set_dispatcher(actions.router, dispatcher_instance))
app.include_router(set_dispatcher(schedulers.router, dispatcher_instance))
app.include_router(set_dispatcher(dispatcher.router, dispatcher_instance))
app.include_router(set_dispatcher(jobs.router, dispatcher_instance))