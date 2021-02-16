"""
These test cases run the API within each test function call, allowing API http calls
to a live and albeit short-lived whendo server.

This class and the fixture, startup_and_shutdown_uvicorn, rely on asynchronous processing.
"""
import time
import pytest
from pydantic import BaseModel
from httpx import AsyncClient
from whendo.core.action import Action
from whendo.core.actions.file_action import FileHeartbeat
from whendo.core.actions.logic_action import ListAction, ListOpMode
from whendo.core.scheduler import TimelyScheduler, Scheduler
from whendo.core.util import FilePathe, resolve_instance
from test.fixtures import port, host, startup_and_shutdown_uvicorn, base_url
from whendo.core.resolver import resolve_action, resolve_scheduler, resolve_file_pathe

@pytest.mark.asyncio
async def test_uvicorn_1(startup_and_shutdown_uvicorn, base_url):
    """
    simple test to see if uvicorn responds to http requests inside the function
    """
    async with AsyncClient(base_url=f"{base_url}/") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json() == 'whengo API server started (unit test)'

@pytest.mark.asyncio
async def test_uvicorn_2(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    add action and scheduler
    """
    await reset_dispatcher(base_url, str(tmp_path))

    output_file = str(tmp_path / 'output.txt')
    xtra={'base_url':base_url}
    action = FileHeartbeat(file=output_file, xtra=xtra)
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, action_name='foo', action=action)
    await add_scheduler(base_url=base_url, scheduler_name='bar', scheduler=scheduler)

@pytest.mark.asyncio
async def test_uvicorn_3(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    add action and scheduler and then schedule the action
    """
    await reset_dispatcher(base_url, str(tmp_path))

    output_file = str(tmp_path / 'output.txt')
    action = FileHeartbeat(file=output_file)
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, action_name='foo', action=action)
    await add_scheduler(base_url=base_url, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name='foo', scheduler_name='bar')
    await assert_job_count(base_url=base_url, n=1)

@pytest.mark.asyncio
async def test_uvicorn_4(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    add action and scheduler, run continuous, and then make sure the action produced file output
    """
    await reset_dispatcher(base_url, str(tmp_path))

    output_file = str(tmp_path / 'output.txt')
    xtra={'base_url':base_url}
    action = FileHeartbeat(file=output_file, xtra=xtra)
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, action_name='foo', action=action)
    await add_scheduler(base_url=base_url, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name='foo', scheduler_name='bar')
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=4)
    lines = None
    with open(action.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

@pytest.mark.asyncio
async def test_uvicorn_logic_action(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ Run two actions within one action. """
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    action3 = ListAction(op_mode=ListOpMode.ALL, action_list=[action1, action2])
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, action_name='foo', action=action3)
    await add_scheduler(base_url=base_url, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name='foo', scheduler_name='bar')
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=4)

    lines = None
    with open(action1.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    lines = None
    with open(action2.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

@pytest.mark.asyncio
async def test_set_action_1(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ unschedule an action. """
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, action_name='foo', action=action1)
    await add_scheduler(base_url=base_url, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name='foo', scheduler_name='bar')
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=4)

    lines = None
    with open(action1.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    await set_action(base_url=base_url, action_name='foo', action=action2)
    await reschedule_action(base_url=base_url, action_name='foo')
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=4)

    lines = None
    with open(action2.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

@pytest.mark.asyncio
async def test_unschedule_action_1(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ unschedule an action. """
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, action_name='foo1', action=action1)
    await add_action(base_url=base_url, action_name='foo2', action=action2)
    await add_scheduler(base_url=base_url, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name='foo1', scheduler_name='bar')
    await schedule_action(base_url=base_url, action_name='foo2', scheduler_name='bar')
    await assert_job_count(base_url=base_url, n=2)

    await unschedule_action(base_url=base_url, action_name='foo1')
    await assert_job_count(base_url=base_url, n=1)
    await get_action(base_url=base_url, action_name='foo1')
    await get_action(base_url=base_url, action_name='foo2')
    await get_scheduler(base_url=base_url, scheduler_name='bar')

@pytest.mark.asyncio
async def test_unschedule_action_2(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ unschedule an action. make sure both schedulers are affected."""
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, action_name='foo1', action=action1)
    await add_action(base_url=base_url, action_name='foo2', action=action2)
    await add_scheduler(base_url=base_url, scheduler_name='bar1', scheduler=scheduler)
    await add_scheduler(base_url=base_url, scheduler_name='bar2', scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name='foo1', scheduler_name='bar1')
    await schedule_action(base_url=base_url, action_name='foo1', scheduler_name='bar2')
    await schedule_action(base_url=base_url, action_name='foo2', scheduler_name='bar1')
    await assert_job_count(base_url=base_url, n=3)

    await unschedule_action(base_url=base_url, action_name='foo1') # two schedulers involved
    await assert_job_count(base_url=base_url, n=1)
    await get_action(base_url=base_url, action_name='foo1')
    await get_action(base_url=base_url, action_name='foo2')
    await get_scheduler(base_url=base_url, scheduler_name='bar1')
    await get_scheduler(base_url=base_url, scheduler_name='bar2')

@pytest.mark.asyncio
async def test_reschedule_action_1(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ schedule action, run it, change it, re-run it """
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, action_name='foo', action=action1)
    await add_scheduler(base_url=base_url, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name='foo', scheduler_name='bar')
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=4)
    lines = None
    with open(action1.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    await set_action(base_url=base_url, action_name='foo', action=action2)
    await reschedule_action(base_url=base_url, action_name='foo')
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=4)
    lines = None
    with open(action2.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    
@pytest.mark.asyncio
async def test_unschedule_scheduler(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ unschedule a sch eduler. """
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    scheduler = TimelyScheduler(interval=1)

    await add_action(base_url=base_url, action_name='foo1', action=action1)
    await add_action(base_url=base_url, action_name='foo2', action=action2)
    await add_scheduler(base_url=base_url, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name='foo1', scheduler_name='bar')
    await schedule_action(base_url=base_url, action_name='foo2', scheduler_name='bar')
    await assert_job_count(base_url=base_url, n=2)

    await unschedule_scheduler(base_url=base_url, scheduler_name='bar')
    await assert_job_count(base_url=base_url, n=0)
    await get_action(base_url=base_url, action_name='foo1')
    await get_action(base_url=base_url, action_name='foo2')
    await get_scheduler(base_url=base_url, scheduler_name='bar')

# helpers

async def get_action(base_url:str, action_name:str):
    """ make sure action exists and resolves properly """
    response = await get(base_url, path=f"/actions/{action_name}")
    assert response.status_code == 200, f"failed to get action ({action_name})"
    retrieved_action = resolve_action(response.json())
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))
    return retrieved_action

async def add_action(base_url:str, action_name:str, action:Action):
    """ add an action and confirm """
    response = await post(base_url=base_url, path=f"/actions/{action_name}", data=action)
    assert response.status_code == 200, f"failed to put action ({action_name})"
    response = await get(base_url, path=f"/actions/{action_name}")
    assert response.status_code == 200, f"failed to get action ({action_name})"
    retrieved_action = resolve_action(response.json())
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))

async def set_action(base_url:str, action_name:str, action:Action):
    """ set an action and confirm """
    response = await put(base_url=base_url, path=f"/actions/{action_name}", data=action)
    assert response.status_code == 200, f"failed to put action ({action_name})"
    response = await get(base_url, path=f"/actions/{action_name}")
    assert response.status_code == 200, f"failed to get action ({action_name})"
    retrieved_action = resolve_action(response.json())
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))

async def unschedule_action(base_url:str, action_name:str):
    response = await get(base_url=base_url, path=f"/actions/{action_name}/unschedule")
    assert response.status_code == 200, f"failed to unschedule action ({action_name})"

async def reschedule_action(base_url:str, action_name:str):
    response = await get(base_url=base_url, path=f"/actions/{action_name}/reschedule")
    assert response.status_code == 200, f"failed to reschedule action ({action_name}) with response({response.json()})"

async def get_scheduler(base_url:str, scheduler_name:str):
    """ make sure scheduler exists and resolves properly """
    response = await get(base_url, path=f"/schedulers/{scheduler_name}")
    assert response.status_code == 200, f"failed to get scheduler ({scheduler_name})"
    retrieved_scheduler = resolve_scheduler(response.json())
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))
    return retrieved_scheduler

async def add_scheduler(base_url:str, scheduler_name:str, scheduler:Scheduler):
    """ add a scheduler and confirm """
    response = await post(base_url=base_url, path=f"/schedulers/{scheduler_name}", data=scheduler)
    assert response.status_code == 200, f"failed to put scheduler ({scheduler_name})"
    response = await get(base_url, path=f"/schedulers/{scheduler_name}")
    assert response.status_code == 200, f"failed to get scheduler ({scheduler_name})"
    retrieved_scheduler = resolve_scheduler(response.json())
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))

async def set_scheduler(base_url:str, scheduler_name:str, scheduler:Scheduler):
    """ add a scheduler and confirm """
    response = await put(base_url=base_url, path=f"/schedulers/{scheduler_name}", data=scheduler)
    assert response.status_code == 200, f"failed to put scheduler ({scheduler_name})"
    response = await get(base_url, path=f"/schedulers/{scheduler_name}")
    assert response.status_code == 200, f"failed to get scheduler ({scheduler_name})"
    retrieved_scheduler = resolve_scheduler(response.json())
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))

async def unschedule_scheduler(base_url:str, scheduler_name:str):
    response = await get(base_url=base_url, path=f"/schedulers/{scheduler_name}/unschedule")
    assert response.status_code == 200, f"failed to unschedule scheduler ({scheduler_name})"

async def schedule_action(base_url:str, scheduler_name:str, action_name:str):
    """ schedule an action """
    response = await get(base_url=base_url, path=f"/schedulers/{scheduler_name}/actions/{action_name}")
    assert response.status_code == 200, f"failed to schedule action ({action_name}) using scheduler ({scheduler_name})"

async def reset_dispatcher(base_url:str, tmp_dir:str):
    """
    usage: reset_dispatcher(base_url, str(tmp_path))
    """

    # set saved_dir to fixture, tmp_path (see usage)
    saved_dir = FilePathe(path=tmp_dir)
    response = await put(base_url=base_url, path='/dispatcher/saved_dir', data=saved_dir)
    assert response.status_code == 200, 'failed to set saved_dir'
    response = await get(base_url=base_url, path='/dispatcher/saved_dir')
    assert response.status_code == 200, 'failed to get saved_dir'
    saved_saved_dir = resolve_file_pathe(response.json())
    assert saved_saved_dir == saved_dir

    # empty the dispatcher and stop the jobs if they're running
    # for uvicorn tests to run in a bunch, these objects need to be 'reset' since
    # evidently the app is shared during the running of the tests
    response = await get(base_url=base_url, path='/dispatcher/clear')
    assert response.status_code == 200, 'failed to get clear dispatcher'
    response = await get(base_url=base_url, path='/jobs/stop') # likely already stopped

async def assert_job_count(base_url:str, n:int):
    response = await get(base_url, '/jobs/count')
    assert response.status_code == 200, 'failed to retrieve job count'
    job_count = response.json()['job_count']
    assert job_count == n, f"expected a job count of ({n}); instead got ({job_count})"

async def run_and_stop_jobs(base_url:str, pause:int):
    response = await get(base_url, '/jobs/run')
    assert response.status_code == 200, 'failed to run jobs'
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

async def delete(base_url:str, path:str):
    async with AsyncClient(base_url=base_url) as ac:
        return await ac.delete(url=path)