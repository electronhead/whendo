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
import whendo.core.actions.file_action as file_x
import whendo.core.actions.dispatch_action as disp_x
import whendo.core.actions.http_action as http_x
import whendo.core.actions.sys_action as sys_x
from whendo.core.actions.list_action import All, Success
from whendo.core.actions.sys_action import SysInfo
from whendo.core.scheduler import Scheduler, Immediately
from whendo.core.schedulers.timed_scheduler import Timely
from whendo.core.dispatcher import Dispatcher
from whendo.core.program import Program
from whendo.core.programs.simple_program import PBEProgram
from whendo.core.server import Server, KeyTagMode
from whendo.core.util import (
    FilePathe,
    resolve_instance,
    DateTime,
    Now,
    Http,
    DateTime2,
    Rez,
)
from whendo.core.resolver import (
    resolve_action,
    resolve_scheduler,
    resolve_file_pathe,
    resolve_server,
)
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
    action = file_x.FileAppend(
        relative_to_output_dir=False, file=output_file, payload={"show": "two"}
    )
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
    action = file_x.FileAppend(
        relative_to_output_dir=False, file=output_file, payload={"show": "two"}
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")
    await assert_job_count(client=client, n=1)


@pytest.mark.asyncio
async def test_client_3(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    add action and scheduler, run timed, and then make sure the action produced file output
    """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    output_file = str(tmp_path / "output.txt")
    action = file_x.FileAppend(
        relative_to_output_dir=False, file=output_file, payload={"show": "two"}
    )
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

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
    )
    action3 = All(actions=[action1, action2])
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

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
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
    await assert_job_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)

    lines = None
    with open(action2.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_unschedule_scheduler(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ unschedule a scheduler. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo1", scheduler_name="bar")
    await schedule_action(client=client, action_name="foo2", scheduler_name="bar")
    await assert_job_count(client=client, n=1)
    await assert_scheduled_action_count(client=client, n=2)

    await unschedule_scheduler(client=client, scheduler_name="bar")
    await assert_job_count(client=client, n=0)
    await assert_scheduled_action_count(client=client, n=0)
    await get_action(client=client, action_name="foo1")
    await get_action(client=client, action_name="foo2")
    await get_scheduler(client=client, scheduler_name="bar")


@pytest.mark.asyncio
async def test_unschedule_all_schedulers(
    startup_and_shutdown_uvicorn, host, port, tmp_path
):
    """ unschedule a scheduler. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo1", scheduler_name="bar")
    await schedule_action(client=client, action_name="foo2", scheduler_name="bar")
    await assert_job_count(client=client, n=1)
    await assert_scheduled_action_count(client=client, n=2)

    await unschedule_all(client=client)
    await assert_job_count(client=client, n=0)
    await assert_scheduled_action_count(client=client, n=0)
    await get_action(client=client, action_name="foo1")
    await get_action(client=client, action_name="foo2")
    await get_scheduler(client=client, scheduler_name="bar")


@pytest.mark.asyncio
async def test_clear_all_scheduling(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ clear all scheduling. """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
    )
    action3 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output3.txt"),
        payload={"show": "two"},
    )
    action4 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output4.txt"),
        payload={"show": "two"},
    )
    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_action(client=client, action_name="foo3", action=action3)
    await add_action(client=client, action_name="foo4", action=action4)

    scheduler = Timely(interval=1)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await add_scheduler(
        client=client, scheduler_name="immediately", scheduler=Immediately()
    )
    program = PBEProgram().prologue("foo4").epilogue("foo3").body_element("bar", "foo2")
    await add_program(client=client, program_name="blink", program=program)

    await schedule_action(client=client, action_name="foo1", scheduler_name="bar")
    await defer_action(
        client=client,
        action_name="foo2",
        scheduler_name="bar",
        wait_until=DateTime(dt=Now.dt() + timedelta(seconds=10)),
    )
    await expire_action(
        client=client,
        action_name="foo2",
        scheduler_name="bar",
        expire_on=DateTime(dt=Now.dt() + timedelta(seconds=15)),
    )
    await schedule_program(
        client=client,
        program_name="blink",
        start_stop=DateTime2(
            dt1=Now.dt() + timedelta(seconds=10), dt2=Now.dt() + timedelta(seconds=15)
        ),
    )
    await assert_job_count(client=client, n=1)
    await assert_scheduled_action_count(client=client, n=1)
    await assert_deferred_action_count(client=client, n=1)
    await assert_expiring_action_count(client=client, n=1)
    await assert_deferred_program_count(client=client, n=1)

    await clear_all_scheduling(client=client)
    await assert_job_count(client=client, n=0)
    await assert_scheduled_action_count(client=client, n=0)
    await assert_deferred_action_count(client=client, n=0)
    await assert_expiring_action_count(client=client, n=0)
    await assert_deferred_program_count(client=client, n=0)
    await get_action(client=client, action_name="foo1")
    await get_action(client=client, action_name="foo2")
    await get_scheduler(client=client, scheduler_name="bar")
    await get_program(client=client, program_name="blink")


@pytest.mark.asyncio
async def test_job_count(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ test job_count """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo1", scheduler_name="bar")
    await schedule_action(client=client, action_name="foo2", scheduler_name="bar")
    await assert_job_count(client=client, n=1)
    await assert_scheduled_action_count(client=client, n=2)


@pytest.mark.asyncio
async def test_schedulers_action_count(
    startup_and_shutdown_uvicorn, host, port, tmp_path
):
    """ tests scheduled action count """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
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

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
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
    assert "bath" in dispatcher.get_scheduled_actions().scheduler_names()
    assert "flea" in dispatcher.get_scheduled_actions().actions("bath")

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

    action = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"show": "two"},
    )
    await add_action(client=client, action_name="foo", action=action)
    await execute_action(client, "foo")

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_execute_action_with_rez(
    startup_and_shutdown_uvicorn, host, port, tmp_path
):
    """ execute an action at a host/port """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output.txt")
    )
    await add_action(client=client, action_name="foo", action=action)
    await execute_action_with_rez(
        client, "foo", rez=Rez(flds={"payload": {"fleas": "abound"}})
    )

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("fleas" in line for line in lines)


@pytest.mark.asyncio
async def test_execute_supplied_action(
    startup_and_shutdown_uvicorn, host, port, tmp_path
):
    """ execute a supplied action """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"show": "two"},
    )

    await client.execute_supplied_action(action)

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_execute_supplied_action_with_rez(
    startup_and_shutdown_uvicorn, host, port, tmp_path
):
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output.txt")
    )
    rez = Rez(flds={"payload": {"higher": "and higher"}})
    await client.execute_supplied_action_with_rez(supplied_action=action, rez=rez)
    time.sleep(2)

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("and higher" in line for line in lines)


@pytest.mark.asyncio
async def test_defer_action(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    Want to observe the scheduling move from deferred state to ready state.
    """

    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
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
        wait_until=DateTime(dt=Now.dt() + timedelta(seconds=0)),
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

    action = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"show": "two"},
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")
    time.sleep(0.5)
    await assert_scheduled_action_count(client=client, n=1)
    await assert_expiring_action_count(client=client, n=0)

    await expire_action(
        client=client,
        action_name="foo",
        scheduler_name="bar",
        expire_on=DateTime(dt=Now.dt() + timedelta(seconds=1)),
    )

    await assert_expiring_action_count(client=client, n=1)
    await assert_scheduled_action_count(client=client, n=1)

    time.sleep(6)

    await assert_expiring_action_count(client=client, n=0)
    await assert_scheduled_action_count(client=client, n=0)


@pytest.mark.asyncio
async def test_immediately(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """
    Want to observe the file was written to and that schedulers_actions was not
    affected.
    """

    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"show": "two"},
    )
    scheduler = Immediately()

    await add_action(client=client, action_name="foo", action=action)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)

    await assert_scheduled_action_count(client=client, n=0)

    await defer_action(
        client=client,
        action_name="foo",
        scheduler_name="bar",
        wait_until=DateTime(dt=Now.dt() + timedelta(seconds=1)),
    )

    await assert_scheduled_action_count(client=client, n=0)

    time.sleep(6)

    await assert_scheduled_action_count(client=client, n=0)

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_program(startup_and_shutdown_uvicorn, host, port, tmp_path):
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
    )
    action3 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output3.txt"),
        payload={"show": "two"},
    )
    scheduler = Timely(interval=1)
    immediately = Immediately()

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_action(client=client, action_name="foo3", action=action3)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await add_scheduler(
        client=client, scheduler_name="immediately", scheduler=immediately
    )

    program = PBEProgram().prologue("foo1").epilogue("foo3").body_element("bar", "foo2")
    await add_program(client=client, program_name="baz", program=program)
    start = Now().dt()
    stop = start + timedelta(seconds=4)
    start_stop = DateTime2(dt1=start, dt2=stop)
    await schedule_program(client=client, program_name="baz", start_stop=start_stop)

    # action1,2,3 doing their things
    await run_and_stop_jobs(client=client, pause=6)
    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    lines = None
    with open(action2.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    lines = None
    with open(action3.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_unschedule_program(startup_and_shutdown_uvicorn, host, port, tmp_path):
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
    )
    action3 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output3.txt"),
        payload={"show": "two"},
    )
    scheduler = Timely(interval=1)
    immediately = Immediately()

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_action(client=client, action_name="foo3", action=action3)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await add_scheduler(
        client=client, scheduler_name="immediately", scheduler=immediately
    )

    program = PBEProgram().prologue("foo1").epilogue("foo3").body_element("bar", "foo2")
    await add_program(client=client, program_name="baz", program=program)

    start = Now.dt() + timedelta(seconds=2)
    stop = start + timedelta(seconds=2)
    start_stop = DateTime2(dt1=start, dt2=stop)

    await schedule_program(client=client, program_name="baz", start_stop=start_stop)
    time.sleep(1)
    await assert_deferred_program_count(client=client, n=1)
    await assert_scheduled_action_count(client=client, n=0)
    await unschedule_program(client=client, program_name="baz")
    await assert_deferred_program_count(client=client, n=0)

    # action1,2,3 not doing their things
    await run_and_stop_jobs(client=client, pause=6)
    with pytest.raises(FileNotFoundError):
        with open(action1.file, "r") as fid:
            lines = fid.readlines()
    with pytest.raises(FileNotFoundError):
        with open(action2.file, "r") as fid:
            lines = fid.readlines()
    with pytest.raises(FileNotFoundError):
        with open(action3.file, "r") as fid:
            lines = fid.readlines()


@pytest.mark.asyncio
async def test_delete_program(startup_and_shutdown_uvicorn, host, port, tmp_path):
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "two"},
    )
    action3 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output3.txt"),
        payload={"show": "two"},
    )
    scheduler = Timely(interval=1)
    immediately = Immediately()

    await add_action(client=client, action_name="foo1", action=action1)
    await add_action(client=client, action_name="foo2", action=action2)
    await add_action(client=client, action_name="foo3", action=action3)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await add_scheduler(
        client=client, scheduler_name="immediately", scheduler=immediately
    )

    program = PBEProgram().prologue("foo1").epilogue("foo3").body_element("bar", "foo2")
    await add_program(client=client, program_name="baz", program=program)
    now = Now().dt()
    start = now + timedelta(seconds=2)
    stop = start + timedelta(seconds=2)
    start_stop = DateTime2(dt1=start, dt2=stop)
    await schedule_program(client=client, program_name="baz", start_stop=start_stop)

    await assert_deferred_program_count(client=client, n=1)
    await assert_scheduled_action_count(client=client, n=0)
    await delete_program(client=client, program_name="baz")
    await assert_deferred_program_count(client=client, n=0)

    # action1,2,3 not doing their things
    await run_and_stop_jobs(client=client, pause=2)
    with pytest.raises(FileNotFoundError):
        with open(action1.file, "r") as fid:
            lines = fid.readlines()
    with pytest.raises(FileNotFoundError):
        with open(action2.file, "r") as fid:
            lines = fid.readlines()
    with pytest.raises(FileNotFoundError):
        with open(action3.file, "r") as fid:
            lines = fid.readlines()


@pytest.mark.asyncio
async def test_success(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ make sure success.execute is a fixed point function """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = Success()
    await add_action(client=client, action_name="success", action=action)
    rez = Rez(result={"fleas": "unite!"})

    await execute_action_with_rez(client=client, action_name="success", rez=rez)


@pytest.mark.asyncio
async def test_file_append_1(startup_and_shutdown_uvicorn, host, port, tmp_path):
    """ test basic use of FileAppend """
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"free": "pyrambium"},
    )
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")

    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("pyrambium" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_2(startup_and_shutdown_uvicorn, host, port, tmp_path):
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"hi": "pyrambium"},
    )
    action2 = SysInfo()
    action3 = All(actions=[action2, action1])
    scheduler = Timely(interval=1)

    await add_action(client=client, action_name="foo", action=action3)
    await add_scheduler(client=client, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(client=client, action_name="foo", scheduler_name="bar")

    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("virtual_memory" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_execute_action(
    startup_and_shutdown_uvicorn, tmp_path, host, port
):
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    server = Server(host=host, port=port, tags={"role": ["pivot"]})
    assert server.port == port
    assert server.host == host
    await add_server(client=client, server_name="test", server=server)
    file_append = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"hi": "pyrambium"},
    )
    info = sys_x.SysInfo()
    execute_action = disp_x.Exec(server_name="test", action_name="file_append")
    actions = All(actions=[info, execute_action])
    timely = Timely(interval=1)

    await add_action(client=client, action_name="file_append", action=file_append)
    await add_action(client=client, action_name="actions", action=actions)
    await add_scheduler(client=client, scheduler_name="timely", scheduler=timely)
    await schedule_action(client=client, action_name="actions", scheduler_name="timely")
    await assert_scheduled_action_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(file_append.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("virtual_memory" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_execute_supplied_action(
    startup_and_shutdown_uvicorn, tmp_path, host, port
):
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    server = Server(host=host, port=port, tags={"role": ["pivot"]})
    assert server.port == port
    assert server.host == host
    await add_server(client=client, server_name="test", server=server)
    file_append = file_x.FileAppend(
        # mode = "D",
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"hi": "pyrambium"},
    )
    info = sys_x.SysInfo()
    execute_action = disp_x.ExecSupplied(server_name="test", action=file_append)
    actions = All(actions=[info, execute_action])
    timely = Timely(interval=1)

    await add_action(client=client, action_name="actions", action=actions)
    await add_scheduler(client=client, scheduler_name="timely", scheduler=timely)
    await schedule_action(client=client, action_name="actions", scheduler_name="timely")
    await assert_scheduled_action_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(file_append.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("virtual_memory" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_execute_action_key_tag(
    startup_and_shutdown_uvicorn, tmp_path, host, port
):
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    server = Server(host=host, port=port, tags={"role": ["pivot"]})
    assert server.port == port
    assert server.host == host
    await add_server(client=client, server_name="test", server=server)
    file_append = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"hi": "pyrambium"},
    )
    info = sys_x.SysInfo()
    execute_action = disp_x.ExecKeyTags(
        key_tags={"role": ["pivot"]}, action_name="file_append"
    )
    actions = All(actions=[info, execute_action])
    timely = Timely(interval=1)

    await add_action(client=client, action_name="file_append", action=file_append)
    await add_action(client=client, action_name="actions", action=actions)
    await add_scheduler(client=client, scheduler_name="timely", scheduler=timely)
    await schedule_action(client=client, action_name="actions", scheduler_name="timely")
    await assert_scheduled_action_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(file_append.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("virtual_memory" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_execute_supplied_action_key_tag(
    startup_and_shutdown_uvicorn, tmp_path, host, port
):
    client = ClientAsync(host=host, port=port)
    await reset_dispatcher(client, str(tmp_path))

    server = Server(host=host, port=port, tags={"role": ["pivot"]})
    assert server.port == port
    assert server.host == host
    await add_server(client=client, server_name="test", server=server)
    file_append = file_x.FileAppend(
        # mode = "D",
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"hi": "pyrambium"},
    )
    info = sys_x.SysInfo()
    execute_action = disp_x.ExecSuppliedKeyTags(
        key_tags={"role": ["pivot"]}, action=file_append
    )
    actions = All(actions=[info, execute_action])
    timely = Timely(interval=1)

    await add_action(client=client, action_name="file_append", action=file_append)
    await add_action(client=client, action_name="actions", action=actions)
    await add_scheduler(client=client, scheduler_name="timely", scheduler=timely)
    await schedule_action(client=client, action_name="actions", scheduler_name="timely")
    await assert_scheduled_action_count(client=client, n=1)

    await run_and_stop_jobs(client=client, pause=2)
    lines = None
    with open(file_append.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("virtual_memory" in line for line in lines)


# ==========================================
# helpers


async def get_program(client: ClientAsync, program_name: str):
    """ add a program and confirm """
    program = await client.get_program(program_name=program_name)
    assert isinstance(program, Program), str(type(program))
    return program


async def add_program(client: ClientAsync, program_name: str, program: Program):
    """ add a program and confirm """
    response = await client.add_program(program_name=program_name, program=program)
    assert (
        response.status_code == 200
    ), f"failed to add program ({program_name}) detail ({response.json()})"
    retrieved_program = await client.get_program(program_name=program_name)
    assert isinstance(retrieved_program, Program), str(type(retrieved_program))


async def set_program(client: ClientAsync, program_name: str, program: Program):
    """ add a program and confirm """
    response = await client.set_program(program_name=program_name, program=program)
    assert response.status_code == 200, f"failed to set program ({program_name})"
    retrieved_program = await client.get_program(program_name=program_name)
    assert isinstance(retrieved_program, Program), str(type(retrieved_program))


async def delete_program(client: ClientAsync, program_name: str):
    """ delete an program """
    response = await client.delete_program(
        program_name=program_name,
    )
    assert response.status_code == 200, f"failed to delete program ({program_name})"


async def schedule_program(
    client: ClientAsync, program_name: str, start_stop: DateTime2
):
    """ schedule an program """
    response = await client.schedule_program(
        program_name=program_name, start_stop=start_stop
    )
    assert response.status_code == 200, f"failed to schedule program ({program_name})"


async def unschedule_program(client: ClientAsync, program_name: str):
    """ schedule an program """
    response = await client.unschedule_program(
        program_name=program_name,
    )
    assert response.status_code == 200, f"failed to unschedule program ({program_name})"


async def add_server(client: ClientAsync, server_name: str, server: Server):
    """ add a server and confirm """
    response = await client.add_server(server_name=server_name, server=server)
    assert response.status_code == 200, f"failed to add server ({server_name})"
    retrieved = await client.get_server(server_name=server_name)
    assert isinstance(retrieved, Server), str(type(retrieved))


async def set_server(client: ClientAsync, server_name: str, server: Server):
    """ set a server and confirm """
    response = await client.set_server(server_name=server_name, server=server)
    assert response.status_code == 200, f"failed to set server ({server_name})"
    retrieved = await client.get_server(server_name=server_name)
    assert isinstance(retrieved, Server), str(type(retrieved))


async def delete_server(client: ClientAsync, server_name: str):
    """ delete a server """
    response = await client.delete_server(server_name=server_name)
    assert response.status_code == 200, f"failed to delete server ({server_name})"


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


async def execute_action(client: ClientAsync, action_name: str):
    response = await client.execute_action(action_name=action_name)
    assert response.status_code == 200, f"failed to execute action ({action_name})"


async def execute_action_with_rez(client: ClientAsync, action_name: str, rez: Rez):
    response = await client.execute_action_with_rez(action_name=action_name, rez=rez)
    assert (
        response.status_code == 200
    ), f"failed to execute action ({action_name}) with rez ({rez})"
    return response.json()


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


async def unschedule_all(client: ClientAsync):
    """
    unschedule all schedulers and actions
    """
    response = await client.unschedule_all_schedulers()
    assert response.status_code == 200, "failed to unschedule all schedulers"


async def clear_all_scheduling(client: ClientAsync):
    """
    unschedule all schedulers and actions
    """
    response = await client.clear_all_scheduling()
    assert response.status_code == 200, "failed to clear all scheduling"


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


async def assert_expiring_action_count(client: ClientAsync, n: int):
    response = await client.expiring_action_count()
    assert response.status_code == 200, "failed to retrieve expiring action count"
    expiring_action_count = response.json()["expiring_action_count"]
    assert expiring_action_count == n, f"expected a expiring action count of ({n})"


async def assert_deferred_program_count(client: ClientAsync, n: int):
    response = await client.deferred_program_count()
    assert response.status_code == 200, "failed to retrieve deferred program count"
    deferred_program_count = response.json()["deferred_program_count"]
    assert deferred_program_count == n, f"expected a deferred program count of ({n})"


async def run_and_stop_jobs(client: ClientAsync, pause: int):
    response = await client.run_jobs()
    assert response.status_code == 200, "failed to start jobs"
    time.sleep(pause)
    response = await client.stop_jobs()
    assert response.status_code == 200, "failed to stop jobs"
