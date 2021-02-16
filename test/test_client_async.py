"""
These test cases run the API within each test function call, allowing API http calls
to a live and albeit short-lived whendo server.

This class and the fixture, startup_and_shutdown_uvicorn, rely on asynchronous processing.
"""
import time
import pytest
from pydantic import BaseModel
from httpx import AsyncClient
from test.client_async import ClientAsync
from whendo.core.action import Action
from whendo.core.actions.file_action import FileHeartbeat
from whendo.core.actions.logic_action import ListAction, ListOpMode
from whendo.core.scheduler import TimelyScheduler, Scheduler
from whendo.core.util import FilePathe, resolve_instance
from test.fixtures import port, host, startup_and_shutdown_uvicorn
from whendo.core.resolver import resolve_action, resolve_scheduler, resolve_file_pathe

@pytest.mark.asyncio
async def test_client_1(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    add action and scheduler
    """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    output_file = str(tmp_path / 'output.txt')
    action = FileHeartbeat(file=output_file)
    scheduler = TimelyScheduler(interval=1)

    await add_action(client=client, action_name='foo', action=action)
    await add_scheduler(client=client, scheduler_name='bar', scheduler=scheduler)

@pytest.mark.asyncio
async def test_client_2(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    add action and scheduler and then schedule the action
    """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    output_file = str(tmp_path / 'output.txt')
    action = FileHeartbeat(file=output_file)
    scheduler = TimelyScheduler(interval=1)

    await add_action(client=client, action_name='foo', action=action)
    await add_scheduler(client=client, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(client=client, action_name='foo', scheduler_name='bar')
    await assert_job_count(client=client, n=1)

@pytest.mark.asyncio
async def test_client_3(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    add action and scheduler, run continuous, and then make sure the action produced file output
    """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    output_file = str(tmp_path / 'output.txt')
    action = FileHeartbeat(file=output_file)
    scheduler = TimelyScheduler(interval=1)

    await add_action(client=client, action_name='foo', action=action)
    await add_scheduler(client=client, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(client=client, action_name='foo', scheduler_name='bar')
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=4)

    lines = None
    with open(action.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

@pytest.mark.asyncio
async def test_client_logic_action(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ Run two actions within one action. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    action3 = ListAction(op_mode=ListOpMode.ALL, action_list=[action1, action2])
    scheduler = TimelyScheduler(interval=1)

    await add_action(client=client, action_name='foo', action=action3)
    await add_scheduler(client=client, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(client=client, action_name='foo', scheduler_name='bar')
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=4)

    lines = None
    with open(action1.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    lines = None
    with open(action2.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

@pytest.mark.asyncio
async def test_set_action_1(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ unschedule an action. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    scheduler = TimelyScheduler(interval=1)

    await add_action(client=client, action_name='foo', action=action1)
    await add_scheduler(client=client, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(client=client, action_name='foo', scheduler_name='bar')
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=4)

    lines = None
    with open(action1.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    await set_action(client=client, action_name='foo', action=action2)
    await reschedule_action(client=client, action_name='foo')
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=4)

    lines = None
    with open(action2.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

@pytest.mark.asyncio
async def test_unschedule_action_1(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ unschedule an action. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    scheduler = TimelyScheduler(interval=1)

    await add_action(client=client, action_name='foo1', action=action1)
    await add_action(client=client, action_name='foo2', action=action2)
    await add_scheduler(client=client, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(client=client, action_name='foo1', scheduler_name='bar')
    await schedule_action(client=client, action_name='foo2', scheduler_name='bar')
    await assert_job_count(client=client, n=2)

    await unschedule_action(client=client, action_name='foo1')
    await assert_job_count(client=client, n=1)
    await get_action(client=client, action_name='foo1')
    await get_action(client=client, action_name='foo2')
    await get_scheduler(client=client, scheduler_name='bar')

@pytest.mark.asyncio
async def test_unschedule_action_2(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ unschedule an action. make sure both schedulers are affected."""
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    scheduler = TimelyScheduler(interval=1)

    await add_action(client=client, action_name='foo1', action=action1)
    await add_action(client=client, action_name='foo2', action=action2)
    await add_scheduler(client=client, scheduler_name='bar1', scheduler=scheduler)
    await add_scheduler(client=client, scheduler_name='bar2', scheduler=scheduler)
    await schedule_action(client=client, action_name='foo1', scheduler_name='bar1')
    await schedule_action(client=client, action_name='foo1', scheduler_name='bar2')
    await schedule_action(client=client, action_name='foo2', scheduler_name='bar1')
    await assert_job_count(client=client, n=3)

    await unschedule_action(client=client, action_name='foo1') # two schedulers involved
    await assert_job_count(client=client, n=1)
    await get_action(client=client, action_name='foo1')
    await get_action(client=client, action_name='foo2')
    await get_scheduler(client=client, scheduler_name='bar1')
    await get_scheduler(client=client, scheduler_name='bar2')

@pytest.mark.asyncio
async def test_reschedule_action_1(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ schedule action, run it, change it, re-run it """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    scheduler = TimelyScheduler(interval=1)

    await add_action(client=client, action_name='foo', action=action1)
    await add_scheduler(client=client, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(client=client, action_name='foo', scheduler_name='bar')
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=4)
    lines = None
    with open(action1.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    await set_action(client=client, action_name='foo', action=action2)
    await reschedule_action(client=client, action_name='foo')
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=4)
    lines = None
    with open(action2.file, 'r') as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
        
@pytest.mark.asyncio
async def test_unschedule_scheduler(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ unschedule a scheduler. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(file=str(tmp_path / 'output1.txt'))
    action2 = FileHeartbeat(file=str(tmp_path / 'output2.txt'))
    scheduler = TimelyScheduler(interval=1)

    await add_action(client=client, action_name='foo1', action=action1)
    await add_action(client=client, action_name='foo2', action=action2)
    await add_scheduler(client=client, scheduler_name='bar', scheduler=scheduler)
    await schedule_action(client=client, action_name='foo1', scheduler_name='bar')
    await schedule_action(client=client, action_name='foo2', scheduler_name='bar')
    await assert_job_count(client=client, n=2)

    await unschedule_scheduler(client=client, scheduler_name='bar')
    await assert_job_count(client=client, n=0)
    await get_action(client=client, action_name='foo1')
    await get_action(client=client, action_name='foo2')
    await get_scheduler(client=client, scheduler_name='bar')

# helpers

async def get_action(client:ClientAsync, action_name:str):
    """ make sure action exists and resolves properly """
    retrieved_action = await client.get_action(action_name=action_name)
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))
    return retrieved_action

async def add_action(client:ClientAsync, action_name:str, action:Action):
    """ add an action and confirm """
    response = await client.add_action(action_name=action_name, action=action)
    assert response.status_code == 200, f"failed to put action ({action_name})"
    retrieved_action = await client.get_action(action_name=action_name)
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))

async def set_action(client:ClientAsync, action_name:str, action:Action):
    """ set an action and confirm """
    response = await client.set_action(action_name=action_name, action=action)
    assert response.status_code == 200, f"failed to put action ({action_name})"
    retrieved_action = await client.get_action(action_name=action_name)
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))

async def unschedule_action(client:ClientAsync, action_name:str):
    response = await client.unschedule_action(action_name=action_name)
    assert response.status_code == 200, f"failed to unschedule action ({action_name})"

async def reschedule_action(client:ClientAsync, action_name:str):
    response = await client.reschedule_action(action_name=action_name)
    assert response.status_code == 200, f"failed to reschedule action ({action_name}) with response({response.json()})"

async def get_scheduler(client:ClientAsync, scheduler_name:str):
    """ make sure scheduler exists and resolves properly """
    retrieved_scheduler = await client.get_scheduler(scheduler_name=scheduler_name)
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))
    return retrieved_scheduler

async def add_scheduler(client:ClientAsync, scheduler_name:str, scheduler:Scheduler):
    """ add a scheduler and confirm """
    response = await client.add_scheduler(scheduler_name=scheduler_name, scheduler=scheduler)
    assert response.status_code == 200, f"failed to put scheduler ({scheduler_name})"
    retrieved_scheduler = await client.get_scheduler(scheduler_name=scheduler_name)
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))

async def set_scheduler(client:ClientAsync, scheduler_name:str, scheduler:Scheduler):
    """ add a scheduler and confirm """
    response = await client.set_scheduler(scheduler_name=scheduler_name, scheduler=scheduler)
    assert response.status_code == 200, f"failed to put scheduler ({scheduler_name})"
    retrieved_scheduler = await client.get_scheduler(scheduler_name=scheduler_name)
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))

async def unschedule_scheduler(client:ClientAsync, scheduler_name:str):
    response = await client.unschedule_scheduler(scheduler_name=scheduler_name)
    assert response.status_code == 200, f"failed to unschedule scheduler ({scheduler_name})"

async def schedule_action(client:ClientAsync, scheduler_name:str, action_name:str):
    """ schedule an action """
    response = await client.schedule_action(scheduler_name=scheduler_name, action_name=action_name)
    assert response.status_code == 200, f"failed to schedule action ({action_name}) using scheduler ({scheduler_name})"

async def reset_dispatcher(client:ClientAsync, tmp_dir:str):
    """
    usage: reset_dispatcher(client, str(tmp_path))
    """
    # set saved_dir to fixture's tmp_path (see usage)
    saved_dir = FilePathe(path=tmp_dir)
    response = await client.set_saved_dir(saved_dir=saved_dir)
    assert response.status_code == 200, 'failed to set saved_dir'
    saved_saved_dir = await client.get_saved_dir()
    assert saved_saved_dir == saved_dir

    # empty the dispatcher and stop the jobs if they're running
    # for uvicorn tests to run in a bunch, these objects need to be 'reset' since
    # evidently the app is shared during the running of the tests
    response = await client.clear_dispatcher()
    assert response.status_code == 200, 'failed to clear dispatcher'
    response = await client.stop_jobs() # likely already stopped

async def assert_job_count(client:ClientAsync, n:int):
    response = await client.job_count()
    assert response.status_code == 200, 'failed to retrieve job count'
    job_count = response.json()['job_count']
    assert job_count == n, f"expected a job count of ({n})"

async def run_and_stop_jobs(client:ClientAsync, pause:int):
    response = await client.run_jobs()
    assert response.status_code == 200, 'failed to start jobs'
    time.sleep(pause)
    response = await client.stop_jobs()
    assert response.status_code == 200, 'failed to stop jobs'