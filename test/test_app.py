"""
These test cases run the API within each test function call, allowing API http calls
to a live and albeit short-lived Pyrambium server.

This class and the fixture, startup_and_shutdown_uvicorn, rely on asynchronous processing.
"""
import time
import pytest
from pydantic import BaseModel
from httpx import AsyncClient
from mothership.action import Action
from mothership.actions.file_action import FileHeartbeat
from mothership.scheduler import TimelyScheduler, Scheduler
from mothership.util import FilePathe, resolve_instance
from test.fixtures import port, host, startup_and_shutdown_uvicorn, base_url
from mothership.resolver import resolve_action, resolve_scheduler

@pytest.mark.asyncio
async def test_uvicorn_1(startup_and_shutdown_uvicorn, base_url):
    """
    simple test to see if uvicorn responds to http requests inside the function
    """
    async with AsyncClient(base_url=f"{base_url}/") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json() == 'Pyrambium API server started (unit test)'

@pytest.mark.asyncio
async def test_uvicorn_2(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    add action and scheduler
    """
    await reset_mothership_continuous(base_url, str(tmp_path))

    output_file = str(tmp_path / 'output.txt')
    xtra={'base_url':base_url}
    action = FileHeartbeat(file=output_file, xtra=xtra)
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, name='foo', action=action)
    await add_scheduler(base_url=base_url, name='bar', scheduler=scheduler)

@pytest.mark.asyncio
async def test_uvicorn_3(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    add action and scheduler and then schedule the action
    """
    await reset_mothership_continuous(base_url, str(tmp_path))

    output_file = str(tmp_path / 'output.txt')
    xtra={'base_url':base_url}
    action = FileHeartbeat(file=output_file, xtra=xtra)
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, name='foo', action=action)
    await add_scheduler(base_url=base_url, name='bar', scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name='foo', scheduler_name='bar')
    await assert_job_count(base_url, 1)

@pytest.mark.asyncio
async def test_uvicorn_4(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    add action and scheduler, run continuous, and then make sure the action produced file output
    """
    await reset_mothership_continuous(base_url, str(tmp_path))

    output_file = str(tmp_path / 'output.txt')
    xtra={'base_url':base_url}
    action = FileHeartbeat(file=output_file, xtra=xtra)
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, name='foo', action=action)
    await add_scheduler(base_url=base_url, name='bar', scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name='foo', scheduler_name='bar')
    await assert_job_count(base_url, 1)

    await start_and_stop_jobs(base_url, 4)
    lines = None
    with open(action.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

# helpers

async def add_action(base_url:str, name:str, action:Action):
    """ add an action and confirm """
    response = await put(base_url=base_url, path=f"/actions/{name}", data=action)
    assert response.status_code == 200, f"failed to put action ({name})"
    response = await get(base_url, path=f"/actions/{name}")
    assert response.status_code == 200, f"failed to get action ({name})"
    retrieved_action = resolve_action(response.json())
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))

async def add_scheduler(base_url:str, name:str, scheduler:Scheduler):
    """ add a scheduler and confirm """
    response = await put(base_url=base_url, path=f"/schedulers/{name}", data=scheduler)
    assert response.status_code == 200, f"failed to put scheduler ({name})"
    response = await get(base_url, path=f"/schedulers/{name}")
    assert response.status_code == 200, f"failed to get scheduler ({name})"
    retrieved_scheduler = resolve_scheduler(response.json())
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))

async def schedule_action(base_url:str, scheduler_name:str, action_name:str):
    """ schedule an action """
    response = await get(base_url=base_url, path=f"/schedulers/{scheduler_name}/actions/{action_name}")
    assert response.status_code == 200, f"failed to schedule action ({action_name}) using scheduler ({scheduler_name})"

async def reset_mothership_continuous(base_url:str, tmp_dir:str):
    """
    usage: reset_mothership_continuous(base_url, str(tmp_path))
    """

    # set saved_dir to fixture, tmp_path (see usage)
    saved_dir = FilePathe(path=tmp_dir)
    response = await put(base_url=base_url, path='/mothership/saved_dir', data=saved_dir)
    assert response.status_code == 200, 'failed to set saved_dir'
    response = await get(base_url=base_url, path='/mothership/saved_dir')
    assert response.status_code == 200, 'failed to get saved_dir'
    saved_saved_dir = resolve_instance(FilePathe, response.json())
    assert saved_saved_dir == saved_dir

    # empty the mothership and stop the jobs if they're running
    # for uvicorn tests to run in a bunch, these objects need to be 'reset' since
    # evidently the app is shared during the running of the tests
    response = await get(base_url=base_url, path='/mothership/clear')
    assert response.status_code == 200, 'failed to get clear mothership'
    response = await get(base_url=base_url, path='/jobs/stop') # likely already stopped

async def assert_job_count(base_url:str, n:int):
    response = await get(base_url, '/jobs/count')
    assert response.status_code == 200, 'failed to retrieve job count'
    job_count = response.json()['job_count']
    assert job_count == n, f"expected a job count of ({n})"

async def start_and_stop_jobs(base_url:str, pause:int):
    response = await get(base_url, '/jobs/start')
    assert response.status_code == 200, 'failed to start jobs'
    time.sleep(pause)
    response = await get(base_url, '/jobs/stop')
    assert response.status_code == 200, 'failed to stop jobs'

async def get(base_url:str, path:str):
    async with AsyncClient(base_url=base_url) as ac:
        return await ac.get(url=path)

async def put(base_url:str, path:str, data:BaseModel):
    async with AsyncClient(base_url=base_url) as ac:
        return await ac.put(url=path, data=data.json())

async def post(base_url:str, path:str, data:BaseModel):
    async with AsyncClient(base_url=base_url) as ac:
        return await ac.post(url=path, data=data.json())

async def patch(base_url:str, path:str, data:dict=None):
    async with AsyncClient(base_url=base_url) as ac:
        return await ac.patch(url=path, data=data)

async def delete(base_url:str, path:str):
    async with AsyncClient(base_url=base_url) as ac:
        return await ac.delete(url=path)