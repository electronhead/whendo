"""
These test cases run the API within each test function call, allowing API http calls
to a live and albeit short-lived whendo server.

This class and the fixture, startup_and_shutdown_uvicorn, rely on asynchronous processing.
"""
import time
import pytest
from datetime import timedelta
from pydantic import BaseModel
from httpx import AsyncClient
from whendo.core.action import Action
from whendo.core.actions.file_action import FileHeartbeat
from whendo.core.actions.logic_action import ListAction, ListOpMode
from whendo.core.actions.http_action import ExecuteAction
from whendo.core.scheduler import Timely, Scheduler, Immediately
from whendo.core.dispatcher import Dispatcher
from whendo.core.util import FilePathe, resolve_instance, DateTime, Now
from whendo.core.resolver import resolve_action, resolve_scheduler, resolve_file_pathe
from .fixtures import port, host, startup_and_shutdown_uvicorn
from .client_async import ClientAsync


@pytest.mark.asyncio
async def test_client_1(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    add action and scheduler
    """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    output_file = str(tmp_path / "output.txt")
    action = FileHeartbeat(relative_to_output_dir=False, file=output_file)
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)


@pytest.mark.asyncio
async def test_client_2(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    add action and scheduler and then schedule the action
    """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    output_file = str(tmp_path / "output.txt")
    action = FileHeartbeat(relative_to_output_dir=False, file=output_file)
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")
    await assert_job_count(client=client, n=1)


@pytest.mark.asyncio
async def test_client_3(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    add action and scheduler, run continuous, and then make sure the action produced file output
    """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    output_file = str(tmp_path / "output.txt")
    action = FileHeartbeat(relative_to_output_dir=False, file=output_file)
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_client_logic_action(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ Run two actions within one action. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    action3 = ListAction(op_mode=ListOpMode.ALL, action_list=[action1, action2])
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action3)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)

    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    lines = None
    with open(action2.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_set_action_1(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ unschedule an action. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action1)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)

    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    await set_action(client=client, action_name="foo", action=action2)
    await reschedule_action(client=client, action_name="foo")
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)

    lines = None
    with open(action2.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_unschedule_action_1(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ unschedule an action. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo1", scheduler_name="bar")
    await schedule_action(client=client, action_name="foo2", scheduler_name="bar")
    await assert_job_count(client=client, n=2)

    await unschedule_action(client=client, action_name="foo1")
    await assert_job_count(client=client, n=1)
    await get_action(client=client, action_name="foo1")
    await get_action(client=client, action_name="foo2")
    await get_scheduler(client=client, scheduler_name="bar")


@pytest.mark.asyncio
async def test_unschedule_action_2(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ unschedule an action. make sure both schedulers are affected."""
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_scheduler(client=client, scheduler_name="bar1", scheduler=scheduler)
    await add_scheduler(client=client, scheduler_name="bar2", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo1", scheduler_name="bar1")
    await schedule_action(client=client, action_name="foo1", scheduler_name="bar2")
    await schedule_action(client=client, action_name="foo2", scheduler_name="bar1")
    await assert_job_count(client=client, n=3)

    await unschedule_action(
        client=client, action_name="foo1"
    )  # two schedulers involved
    await assert_job_count(client=client, n=1)
    await get_action(client=client, action_name="foo1")
    await get_action(client=client, action_name="foo2")
    await get_scheduler(client=client, scheduler_name="bar1")
    await get_scheduler(client=client, scheduler_name="bar2")


@pytest.mark.asyncio
async def test_reschedule_action_1(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ schedule action, run it, change it, re-run it """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action1)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    await set_action(client=client, action_name="foo", action=action2)
    await reschedule_action(client=client, action_name="foo")
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(action2.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_unschedule_scheduler(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ unschedule a scheduler. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo1", scheduler_name="bar")
    await schedule_action(client=client, action_name="foo2", scheduler_name="bar")
    await assert_job_count(client=client, n=2)

    await unschedule_scheduler(client=client, scheduler_name="bar")
    await assert_job_count(client=client, n=0)
    await get_action(client=client, action_name="foo1")
    await get_action(client=client, action_name="foo2")
    await get_scheduler(client=client, scheduler_name="bar")


@pytest.mark.asyncio
async def test_job_count(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ test job_count """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo1", scheduler_name="bar")
    await schedule_action(client=client, action_name="foo2", scheduler_name="bar")
    await assert_job_count(client=client, n=2)


@pytest.mark.asyncio
async def test_schedulers_action_count(
    startup_and_shutdown_uvicorn, host, port, tmp_path
):
    """ tests scheduled action count """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo1", scheduler_name="bar")
    await schedule_action(client=client, action_name="foo2", scheduler_name="bar")
    await assert_scheduled_action_count(client=client, n=2)


@pytest.mark.asyncio
async def test_replace_dispatcher(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ replace innards of the active dispatcher """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    saved_dir = await get_saved_dir(client=client)

    action1 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action1)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")
    await assert_job_count(client=client, n=1)
    await assert_scheduled_action_count(client=client, n=1)

    # action1 doing its thing
    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    # replacement dispatcher
    replacement = Dispatcher()  # no saved_dir
    replacement.add_action("flea", action2)
    replacement.add_scheduler("bath", scheduler)
    replacement.schedule_action(action_name="flea", scheduler_name="bath")
    assert replacement.get_saved_dir() is None
    await assert_job_count(client=client, n=1)

    # do the business
    await replace_dispatcher(client=client, replacement=replacement)

    # check the business before checking the behavior of action2
    await assert_scheduled_action_count(client=client, n=1)
    await assert_job_count(client=client, n=0)

    action3 = await get_action(client=client, action_name="flea")
    assert action3 is not None
    assert action3.file.count("output2") > 0

    scheduler2 = await get_scheduler(client=client, scheduler_name="bath")
    assert scheduler2 is not None
    assert scheduler2.interval == 1

    new_saved_dir = await get_saved_dir(client=client)
    assert new_saved_dir == saved_dir

    dispatcher = await load_dispatcher(client=client)
    assert "flea" in dispatcher.get_actions()
    assert "bath" in dispatcher.get_schedulers()
    assert "bath" in dispatcher.get_schedulers_actions()
    assert "flea" in dispatcher.get_schedulers_actions()["bath"]

    # add the job
    await assert_scheduled_action_count(client=client, n=1)
    await reschedule_all(client=client)
    await assert_job_count(client=client, n=1)

    # did action2 do what it was supposed to do?
    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(action2.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_execute_action(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ execute an action at a host/port """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output.txt")
    )
    await add_action(client=client, action_name="foo", action=action)

    execute_action = ExecuteActionAsync(
        client=client, host=host, port=port, action_name="foo"
    )
    await execute_action.execute()
    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_execute_supplied_action(
    startup_and_shutdown_uvicorn, host, port, tmp_path
):
    """ execute a supplied action """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output.txt")
    )

    await client.execute_supplied_action(action)

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_defer_action(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    Want to observe the scheduling move from deferred state to ready state.
    """

    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)

    await assert_deferred_action_count(client=client, n=0)
    await assert_scheduled_action_count(client=client, n=0)

    await defer_action(
        client=client,
        action_name="foo",
        scheduler_name="bar",
        wait_until=DateTime(date_time=Now.dt() + timedelta(seconds=0)),
    )

    await assert_deferred_action_count(client=client, n=1)
    await assert_scheduled_action_count(client=client, n=0)

    time.sleep(6)

    await assert_deferred_action_count(client=client, n=0)
    await assert_scheduled_action_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_expire_action(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    Want to observe that an expired action is no longer scheduled
    """

    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")

    await assert_expired_action_count(client=client, n=0)
    await assert_scheduled_action_count(client=client, n=1)

    await expire_action(
        client=client,
        action_name="foo",
        scheduler_name="bar",
        expire_on=DateTime(date_time=Now.dt() + timedelta(seconds=1)),
    )

    await assert_expired_action_count(client=client, n=1)
    await assert_scheduled_action_count(client=client, n=1)

    time.sleep(6)

    await assert_expired_action_count(client=client, n=0)
    await assert_scheduled_action_count(client=client, n=0)


@pytest.mark.asyncio
async def test_immediately(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    Want to observe the file was written to and that schedulers_actions was not
    affected.
    """

    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = FileHeartbeat(
        relative_to_output_dir=False, file=str(tmp_path / "output.txt")
    )
    scheduler = Immediately()

    await add_action(client=client, action_name="foo", action=action)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)

    await assert_scheduled_action_count(client=client, n=0)

    await defer_action(
        client=client,
        action_name="foo",
        scheduler_name="bar",
        wait_until=DateTime(date_time=Now.dt() + timedelta(seconds=1)),
    )

    await assert_scheduled_action_count(client=client, n=0)

    time.sleep(6)

    await assert_scheduled_action_count(client=client, n=0)

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


# helpers


async def get_action(client: ClientAsync, action_name: str):
    """ make sure action exists and resolves properly """
    retrieved_action = await client.get_action(action_name=action_name)
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))
    return retrieved_action


async def add_action(client: ClientAsync, action_name: str, action: Action):
    """ add an action and confirm """
    response = await client.add_action(action_name=action_name, action=action)
    assert response.status_code == 200, f"failed to put action ({action_name})"
    retrieved_action = await client.get_action(action_name=action_name)
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))


async def set_action(client: ClientAsync, action_name: str, action: Action):
    """ set an action and confirm """
    response = await client.set_action(action_name=action_name, action=action)
    assert response.status_code == 200, f"failed to put action ({action_name})"
    retrieved_action = await client.get_action(action_name=action_name)
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))


async def unschedule_action(client: ClientAsync, action_name: str):
    response = await client.unschedule_action(action_name=action_name)
    assert response.status_code == 200, f"failed to unschedule action ({action_name})"


async def reschedule_action(client: ClientAsync, action_name: str):
    response = await client.reschedule_action(action_name=action_name)
    assert (
        response.status_code == 200
    ), f"failed to reschedule action ({action_name}) with response({response.json()})"


async def get_scheduler(client: ClientAsync, scheduler_name: str):
    """ make sure scheduler exists and resolves properly """
    retrieved_scheduler = await client.get_scheduler(scheduler_name=scheduler_name)
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))
    return retrieved_scheduler


async def add_scheduler(client: ClientAsync, scheduler_name: str, scheduler: Scheduler):
    """ add a scheduler and confirm """
    response = await client.add_scheduler(
        scheduler_name=scheduler_name, scheduler=scheduler
    )
    assert response.status_code == 200, f"failed to put scheduler ({scheduler_name})"
    retrieved_scheduler = await client.get_scheduler(scheduler_name=scheduler_name)
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))


async def set_scheduler(client: ClientAsync, scheduler_name: str, scheduler: Scheduler):
    """ add a scheduler and confirm """
    response = await client.set_scheduler(
        scheduler_name=scheduler_name, scheduler=scheduler
    )
    assert response.status_code == 200, f"failed to put scheduler ({scheduler_name})"
    retrieved_scheduler = await client.get_scheduler(scheduler_name=scheduler_name)
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))


async def unschedule_scheduler(client: ClientAsync, scheduler_name: str):
    response = await client.unschedule_scheduler(scheduler_name=scheduler_name)
    assert (
        response.status_code == 200
    ), f"failed to unschedule scheduler ({scheduler_name})"


async def schedule_action(client: ClientAsync, scheduler_name: str, action_name: str):
    """ schedule an action """
    response = await client.schedule_action(
        scheduler_name=scheduler_name, action_name=action_name
    )
    assert (
        response.status_code == 200
    ), f"failed to schedule action ({action_name}) using scheduler ({scheduler_name})"


async def defer_action(
    client: ClientAsync, scheduler_name: str, action_name: str, wait_until: DateTime
):
    """ defer an action """
    response = await client.defer_action(
        scheduler_name=scheduler_name, action_name=action_name, wait_until=wait_until
    )
    assert (
        response.status_code == 200
    ), f"failed to defer action ({action_name}) using scheduler ({scheduler_name})"


async def expire_action(
    client: ClientAsync, scheduler_name: str, action_name: str, expire_on: DateTime
):
    """ expire an action """
    response = await client.expire_action(
        scheduler_name=scheduler_name, action_name=action_name, expire_on=expire_on
    )
    assert (
        response.status_code == 200
    ), f"failed to expire action ({action_name}) using scheduler ({scheduler_name})"


async def load_dispatcher(client: ClientAsync):
    """ return the saved dispatcher """
    retrieved_dispatcher = await client.load_dispatcher()
    assert isinstance(retrieved_dispatcher, Dispatcher), str(type(retrieved_dispatcher))
    return retrieved_dispatcher


async def get_saved_dir(client: ClientAsync):
    """ return saved_dir """
    retrieved_file_path = await client.get_saved_dir()
    assert isinstance(retrieved_file_path, FilePathe), str(type(retrieved_file_path))
    return retrieved_file_path


async def replace_dispatcher(client: ClientAsync, replacement: Dispatcher):
    """
    replace a dispatcher
    """
    response = await client.replace_dispatcher(replacement)
    assert (
        response.status_code == 200
    ), f"failed to replace the dispatcher ({response.json()}"


async def reschedule_all(client: ClientAsync):
    """
    reschedule all schedulers and actions
    """
    response = await client.reschedule_all_schedulers()
    assert response.status_code == 200, "failed to reschedule all schedulers"


async def reset_dispatcher(client: ClientAsync, tmp_dir: str):
    """
    usage: reset_dispatcher(client, str(tmp_path))
    """
    # set saved_dir to fixture's tmp_path (see usage)
    saved_dir = FilePathe(path=tmp_dir)
    response = await client.set_saved_dir(saved_dir=saved_dir)
    assert response.status_code == 200, "failed to set saved_dir"
    saved_saved_dir = await client.get_saved_dir()
    assert saved_saved_dir == saved_dir

    # empty the dispatcher and stop the jobs if they're running
    # for uvicorn tests to run in a bunch, these objects need to be 'reset' since
    # evidently the app is shared during the running of the tests
    response = await client.clear_dispatcher()
    assert response.status_code == 200, "failed to clear dispatcher"
    response = await client.stop_jobs()  # likely already stopped


async def assert_job_count(client: ClientAsync, n: int):
    response = await client.job_count()
    assert response.status_code == 200, "failed to retrieve job count"
    job_count = response.json()["job_count"]
    assert job_count == n, f"expected a job count of ({n})"


async def assert_scheduled_action_count(client: ClientAsync, n: int):
    response = await client.scheduled_action_count()
    assert response.status_code == 200, "failed to retrieve job count"
    action_count = response.json()["action_count"]
    assert action_count == n, f"expected an action count of ({n})"


async def assert_deferred_action_count(client: ClientAsync, n: int):
    response = await client.deferred_action_count()
    assert response.status_code == 200, "failed to retrieve deferred action count"
    deferred_action_count = response.json()["deferred_action_count"]
    assert deferred_action_count == n, f"expected a deferred action count of ({n})"


async def assert_expired_action_count(client: ClientAsync, n: int):
    response = await client.expired_action_count()
    assert response.status_code == 200, "failed to retrieve expired action count"
    expired_action_count = response.json()["expired_action_count"]
    assert expired_action_count == n, f"expected a expired action count of ({n})"


async def run_and_stop_jobs(client: ClientAsync, pause: int):
    response = await client.run_jobs()
    assert response.status_code == 200, "failed to start jobs"
    time.sleep(pause)
    response = await client.stop_jobs()
    assert response.status_code == 200, "failed to stop jobs"


class ExecuteActionAsync(ExecuteAction):
    """
    Execute an action at host:port.
    """

    client: ClientAsync

    async def execute(self, tag: str = None, scheduler_info: dict = None):
        await self.client.execute_action(self.action_name)
