"""
These test cases run the API within each test function call, allowing API http calls
to a live and albeit short-lived whendo server.

This class and the fixture, startup_and_shutdown_uvicorn, rely on asynchronous processing.
"""
import time
import pytest
import json
from pydantic import BaseModel
from httpx import AsyncClient
from datetime import timedelta
from whendo.core.action import Action, ActionRez
import whendo.core.actions.file_action as file_x
import whendo.core.actions.dispatch_action as disp_x
import whendo.core.actions.http_action as http_x
import whendo.core.actions.sys_action as sys_x
from whendo.core.actions.list_action import All, Success, Vals
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
    Output,
    DateTime,
    Now,
    DateTime2,
    Rez,
)
from whendo.core.resolver import (
    resolve_action,
    resolve_scheduler,
    resolve_file_pathe,
    resolve_program,
    resolve_server,
    resolve_instance,
    resolve_rez,
)
from .fixtures import port, host, startup_and_shutdown_uvicorn, base_url
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_uvicorn_1(startup_and_shutdown_uvicorn, base_url):
    """
    simple test to see if uvicorn responds to http requests inside the function
    """
    async with AsyncClient(base_url=f"{base_url}/") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json() == "whengo API server started (unit test)"


@pytest.mark.asyncio
async def test_uvicorn_2(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    add action and scheduler
    """
    await reset_dispatcher(base_url, str(tmp_path))

    output_file = str(tmp_path / "output.txt")
    xtra = {"base_url": base_url}
    action = file_x.FileAppend(relative_to_output_dir=False, file=output_file)
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo", action=action)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)


@pytest.mark.asyncio
async def test_uvicorn_3(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    add action and scheduler and then schedule the action
    """
    await reset_dispatcher(base_url, str(tmp_path))

    output_file = str(tmp_path / "output.txt")
    action = file_x.FileAppend(relative_to_output_dir=False, file=output_file)
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo", action=action)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo", scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=1)


@pytest.mark.asyncio
async def test_uvicorn_4(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    add action and scheduler, run timed, and then make sure the action produced file output
    """
    await reset_dispatcher(base_url, str(tmp_path))

    output_file = str(tmp_path / "output.txt")
    xtra = {"base_url": base_url}
    action = file_x.FileAppend(
        relative_to_output_dir=False, file=output_file, payload={"show": "two"}
    )
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo", action=action)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo", scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_uvicorn_logic_action(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ Run two actions within one action. """
    await reset_dispatcher(base_url, str(tmp_path))

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

    await add_action(base_url=base_url, action_name="foo", action=action3)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo", scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)

    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    lines = None
    with open(action2.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_set_action_1(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ unschedule an action. """
    await reset_dispatcher(base_url, str(tmp_path))

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

    await add_action(base_url=base_url, action_name="foo", action=action1)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo", scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)

    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    await set_action(base_url=base_url, action_name="foo", action=action2)
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)

    lines = None
    with open(action2.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_reschedule_action_1(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ schedule action, run it, change it, re-run it """
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"show": "two"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"show": "three"},
    )
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo", action=action1)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo", scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1

    await set_action(base_url=base_url, action_name="foo", action=action2)
    await assert_job_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(action2.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_unschedule_scheduler(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ unschedule a scheduler. """
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo1", action=action1)
    await add_action(base_url=base_url, action_name="foo2", action=action2)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo1", scheduler_name="bar")
    await schedule_action(base_url=base_url, action_name="foo2", scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=2)

    await unschedule_scheduler(base_url=base_url, scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=0)
    await assert_scheduled_action_count(base_url=base_url, n=0)
    await get_action(base_url=base_url, action_name="foo1")
    await get_action(base_url=base_url, action_name="foo2")
    await get_scheduler(base_url=base_url, scheduler_name="bar")


@pytest.mark.asyncio
async def test_unschedule_all_schedulers(
    startup_and_shutdown_uvicorn, base_url, tmp_path
):
    """ unschedule a scheduler. """
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo1", action=action1)
    await add_action(base_url=base_url, action_name="foo2", action=action2)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo1", scheduler_name="bar")
    await schedule_action(base_url=base_url, action_name="foo2", scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=2)

    await unschedule_all(base_url=base_url)
    await assert_job_count(base_url=base_url, n=0)
    await assert_scheduled_action_count(base_url=base_url, n=0)
    await get_action(base_url=base_url, action_name="foo1")
    await get_action(base_url=base_url, action_name="foo2")
    await get_scheduler(base_url=base_url, scheduler_name="bar")


@pytest.mark.asyncio
async def test_unschedule_all_scheduling(
    startup_and_shutdown_uvicorn, base_url, tmp_path
):
    """ unschedule a scheduler. """
    await reset_dispatcher(base_url, str(tmp_path))

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

    await add_action(base_url=base_url, action_name="foo1", action=action1)
    await add_action(base_url=base_url, action_name="foo2", action=action2)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo1", scheduler_name="bar")
    await schedule_action(base_url=base_url, action_name="foo2", scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=2)

    await unschedule_all(base_url=base_url)
    await assert_job_count(base_url=base_url, n=0)
    await assert_scheduled_action_count(base_url=base_url, n=0)
    await get_action(base_url=base_url, action_name="foo1")
    await get_action(base_url=base_url, action_name="foo2")
    await get_scheduler(base_url=base_url, scheduler_name="bar")


@pytest.mark.asyncio
async def test_clear_all_scheduling(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ clear all scheduling. """
    await reset_dispatcher(base_url, str(tmp_path))

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
    await add_action(base_url=base_url, action_name="foo1", action=action1)
    await add_action(base_url=base_url, action_name="foo2", action=action2)
    await add_action(base_url=base_url, action_name="foo3", action=action3)
    await add_action(base_url=base_url, action_name="foo4", action=action4)

    scheduler = Timely(interval=1)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await add_scheduler(
        base_url=base_url, scheduler_name="immediately", scheduler=Immediately()
    )
    program = PBEProgram().prologue("foo4").epilogue("foo3").body_element("bar", "foo2")
    await add_program(base_url=base_url, program_name="blink", program=program)

    await schedule_action(base_url=base_url, action_name="foo1", scheduler_name="bar")
    await defer_action(
        base_url=base_url,
        action_name="foo2",
        scheduler_name="bar",
        wait_until=DateTime(dt=Now.dt() + timedelta(seconds=10)),
    )
    await expire_action(
        base_url=base_url,
        action_name="foo2",
        scheduler_name="bar",
        expire_on=DateTime(dt=Now.dt() + timedelta(seconds=15)),
    )
    await schedule_program(
        base_url=base_url,
        program_name="blink",
        start_stop=DateTime2(
            dt1=Now.dt() + timedelta(seconds=10), dt2=Now.dt() + timedelta(seconds=15)
        ),
    )
    await assert_job_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=1)
    await assert_deferred_action_count(base_url=base_url, n=1)
    await assert_expiring_action_count(base_url=base_url, n=1)
    await assert_deferred_program_count(base_url=base_url, n=1)

    await clear_all_scheduling(base_url=base_url)
    await assert_job_count(base_url=base_url, n=0)
    await assert_scheduled_action_count(base_url=base_url, n=0)
    await assert_deferred_action_count(base_url=base_url, n=0)
    await assert_expiring_action_count(base_url=base_url, n=0)
    await assert_deferred_program_count(base_url=base_url, n=0)
    await get_action(base_url=base_url, action_name="foo1")
    await get_action(base_url=base_url, action_name="foo2")
    await get_scheduler(base_url=base_url, scheduler_name="bar")
    await get_program(base_url=base_url, program_name="blink")


@pytest.mark.asyncio
async def test_job_count(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ test job_count """
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo1", action=action1)
    await add_action(base_url=base_url, action_name="foo2", action=action2)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo1", scheduler_name="bar")
    await schedule_action(base_url=base_url, action_name="foo2", scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=2)


@pytest.mark.asyncio
async def test_schedulers_action_count(
    startup_and_shutdown_uvicorn, base_url, tmp_path
):
    """ tests scheduled action count """
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output1.txt")
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output2.txt")
    )
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo1", action=action1)
    await add_action(base_url=base_url, action_name="foo2", action=action2)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo1", scheduler_name="bar")
    await schedule_action(base_url=base_url, action_name="foo2", scheduler_name="bar")
    await assert_scheduled_action_count(base_url=base_url, n=2)


@pytest.mark.asyncio
async def test_replace_dispatcher(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ replace innards of the active dispatcher """
    await reset_dispatcher(base_url, str(tmp_path))

    saved_dir = await get_saved_dir(base_url=base_url)

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

    await add_action(base_url=base_url, action_name="foo", action=action1)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo", scheduler_name="bar")
    await assert_job_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=1)

    # action1 doing its thing
    await run_and_stop_jobs(base_url=base_url, pause=2)
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
    await assert_job_count(base_url=base_url, n=1)

    # do the business
    await replace_dispatcher(base_url=base_url, replacement=replacement)

    # check the business before checking the behavior of action2
    await assert_scheduled_action_count(base_url=base_url, n=1)
    await assert_job_count(base_url=base_url, n=0)

    action3 = await get_action(base_url=base_url, action_name="flea")
    assert action3 is not None
    assert action3.file.count("output2") > 0

    scheduler2 = await get_scheduler(base_url=base_url, scheduler_name="bath")
    assert scheduler2 is not None
    assert scheduler2.interval == 1

    new_saved_dir = await get_saved_dir(base_url=base_url)
    assert new_saved_dir == saved_dir

    dispatcher = await load_dispatcher(base_url=base_url)
    assert "flea" in dispatcher.get_actions()
    assert "bath" in dispatcher.get_schedulers()
    assert "bath" in dispatcher.get_scheduled_actions().scheduler_names()
    assert "flea" in dispatcher.get_scheduled_actions().actions("bath")

    # add the job
    await assert_scheduled_action_count(base_url=base_url, n=1)
    await reschedule_all(base_url=base_url)
    await assert_job_count(base_url=base_url, n=1)

    # did action2 do what it was supposed to do?
    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(action2.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_execute_action(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ execute an action at a host/port """
    await reset_dispatcher(base_url, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"show": "two"},
    )
    await add_action(base_url=base_url, action_name="foo", action=action)

    await execute_action(base_url=base_url, action_name="foo")

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_execute_action_with_rez(
    startup_and_shutdown_uvicorn, base_url, tmp_path
):
    """ execute an action at a host/port """
    await reset_dispatcher(base_url, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output.txt")
    )
    await add_action(base_url=base_url, action_name="foo", action=action)

    await execute_action_with_rez(
        base_url=base_url,
        action_name="foo",
        rez=Rez(flds={"payload": {"fleas": "abound"}}),
    )

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("fleas" in line for line in lines)


@pytest.mark.asyncio
async def test_execute_supplied_action(
    startup_and_shutdown_uvicorn, base_url, tmp_path
):
    """ execute a supplied action """
    await reset_dispatcher(base_url, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"show": "time"},
    )

    await post(base_url, "/execution", action)

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("show" in line for line in lines)


@pytest.mark.asyncio
async def test_execute_supplied_action_with_rez(
    startup_and_shutdown_uvicorn, base_url, tmp_path
):
    """ execute a supplied action """
    await reset_dispatcher(base_url, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output.txt")
    )
    rez = Rez(flds={"payload": {"higher": "and higher"}})
    # action_rez = ActionRez(action=action, rez=rez)
    # await post(base_url, "/execution/with_rez", action_rez)
    action.complete_fields(rez=rez)
    await post(base_url, "/execution", action)
    time.sleep(4)

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("and higher" in line for line in lines)


@pytest.mark.asyncio
async def test_defer_action(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    Want to observe [1] the scheduling moved from deferred state to ready state and
    [2] the scheduled action having an effect.
    """

    await reset_dispatcher(base_url, str(tmp_path))
    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"over": 3},
    )
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo", action=action1)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)

    await assert_deferred_action_count(base_url=base_url, n=0)
    await assert_scheduled_action_count(base_url=base_url, n=0)

    await defer_action(
        base_url=base_url,
        action_name="foo",
        scheduler_name="bar",
        wait_until=DateTime(dt=Now.dt() + timedelta(seconds=0)),
    )

    await assert_deferred_action_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=0)

    time.sleep(4)

    await assert_deferred_action_count(base_url=base_url, n=0)
    await assert_scheduled_action_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("3" in line for line in lines)


@pytest.mark.asyncio
async def test_expire_action(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    Want to observe [1] the scheduling moved from deferred state to ready state and
    [2] the scheduled action having an effect.
    """

    await reset_dispatcher(base_url, str(tmp_path))
    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"under": 3.2},
    )
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo", action=action1)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo", scheduler_name="bar")

    await assert_expiring_action_count(base_url=base_url, n=0)
    await assert_scheduled_action_count(base_url=base_url, n=1)

    await expire_action(
        base_url=base_url,
        action_name="foo",
        scheduler_name="bar",
        expire_on=DateTime(dt=Now.dt() + timedelta(seconds=1)),
    )

    await assert_expiring_action_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=1)

    time.sleep(6)

    await assert_expiring_action_count(base_url=base_url, n=0)
    await assert_scheduled_action_count(base_url=base_url, n=0)


@pytest.mark.asyncio
async def test_immediately(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """
    Want to observe the file was written to and that schedulers_actions was not
    affected.
    """

    await reset_dispatcher(base_url, str(tmp_path))
    action = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"oh": "out put #1"},
    )
    scheduler = Immediately()

    await add_action(base_url=base_url, action_name="foo", action=action)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)

    await assert_scheduled_action_count(base_url=base_url, n=0)

    await defer_action(
        base_url=base_url,
        action_name="foo",
        scheduler_name="bar",
        wait_until=DateTime(dt=Now.dt() + timedelta(seconds=1)),
    )

    await assert_deferred_action_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=0)

    time.sleep(6)

    await assert_deferred_action_count(base_url=base_url, n=0)
    await assert_scheduled_action_count(base_url=base_url, n=0)

    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


@pytest.mark.asyncio
async def test_program(startup_and_shutdown_uvicorn, base_url, tmp_path):
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"oh": "out put #1"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"oh": "out put #2"},
    )
    action3 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output3.txt"),
        payload={"oh": "out put #3"},
    )
    scheduler = Timely(interval=1)
    immediately = Immediately()

    await add_action(base_url=base_url, action_name="foo1", action=action1)
    await add_action(base_url=base_url, action_name="foo2", action=action2)
    await add_action(base_url=base_url, action_name="foo3", action=action3)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await add_scheduler(
        base_url=base_url, scheduler_name="immediately", scheduler=immediately
    )

    program = PBEProgram().prologue("foo1").epilogue("foo3").body_element("bar", "foo2")
    await add_program(base_url=base_url, program_name="baz", program=program)
    start_stop = DateTime2(dt1=Now().dt(), dt2=Now().dt() + timedelta(seconds=4))
    await schedule_program(base_url=base_url, program_name="baz", start_stop=start_stop)

    # action1,2,3 doing their things
    await run_and_stop_jobs(base_url=base_url, pause=6)
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
async def test_unschedule_program(startup_and_shutdown_uvicorn, base_url, tmp_path):
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"oh": "out put 1"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"oh": "out put #2"},
    )
    action3 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output3.txt"),
        payload={"oh": "out put #3"},
    )
    scheduler = Timely(interval=1)
    immediately = Immediately()

    await add_action(base_url=base_url, action_name="foo1", action=action1)
    await add_action(base_url=base_url, action_name="foo2", action=action2)
    await add_action(base_url=base_url, action_name="foo3", action=action3)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await add_scheduler(
        base_url=base_url, scheduler_name="immediately", scheduler=immediately
    )

    program = PBEProgram().prologue("foo1").epilogue("foo3").body_element("bar", "foo2")
    await add_program(base_url=base_url, program_name="baz", program=program)
    start = Now.dt() + timedelta(seconds=2)
    stop = start + timedelta(seconds=2)
    start_stop = DateTime2(dt1=start, dt2=stop)

    await schedule_program(base_url=base_url, program_name="baz", start_stop=start_stop)
    time.sleep(1)
    await assert_deferred_program_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=0)
    await unschedule_program(base_url=base_url, program_name="baz")
    await assert_deferred_program_count(base_url=base_url, n=0)

    # action1,2,3 not doing their things
    await run_and_stop_jobs(base_url=base_url, pause=4)
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
async def test_delete_program(startup_and_shutdown_uvicorn, base_url, tmp_path):
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output1.txt"),
        payload={"oh": "out put #1"},
    )
    action2 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output2.txt"),
        payload={"oh": "out put #2"},
    )
    action3 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output3.txt"),
        payload={"oh": "out put #3"},
    )
    scheduler = Timely(interval=1)
    immediately = Immediately()

    await add_action(base_url=base_url, action_name="foo1", action=action1)
    await add_action(base_url=base_url, action_name="foo2", action=action2)
    await add_action(base_url=base_url, action_name="foo3", action=action3)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await add_scheduler(
        base_url=base_url, scheduler_name="immediately", scheduler=immediately
    )

    program = PBEProgram().prologue("foo1").epilogue("foo3").body_element("bar", "foo2")
    await add_program(base_url=base_url, program_name="baz", program=program)
    start_stop = DateTime2(dt1=Now().dt(), dt2=Now().dt() + timedelta(seconds=4))
    await schedule_program(base_url=base_url, program_name="baz", start_stop=start_stop)
    await assert_deferred_program_count(base_url=base_url, n=1)
    await assert_scheduled_action_count(base_url=base_url, n=0)
    await delete_program(base_url=base_url, program_name="baz")
    await assert_deferred_program_count(base_url=base_url, n=0)

    # action1,2,3 not doing their things
    await run_and_stop_jobs(base_url=base_url, pause=6)
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
async def test_success(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ test fixed point """
    await reset_dispatcher(base_url, str(tmp_path))

    action = Success()
    await add_action(base_url=base_url, action_name="success", action=action)
    rez = Rez(result={"fleas": "unite!"})

    await execute_action_with_rez(base_url=base_url, action_name="success", rez=rez)


@pytest.mark.asyncio
async def test_file_append_1(startup_and_shutdown_uvicorn, base_url, tmp_path):
    """ test basic use of file_x.FileAppend """
    await reset_dispatcher(base_url, str(tmp_path))

    action = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"free": "pyrambium"},
    )
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo", action=action)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo", scheduler_name="bar")

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(action.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("pyrambium" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_2(startup_and_shutdown_uvicorn, base_url, tmp_path):
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"hi": "pyrambium"},
    )
    action2 = SysInfo()
    action3 = All(actions=[action2, action1])
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo", action=action3)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo", scheduler_name="bar")

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("virtual_memory" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_3(startup_and_shutdown_uvicorn, base_url, tmp_path):
    await reset_dispatcher(base_url, str(tmp_path))

    action1 = file_x.FileAppend(
        relative_to_output_dir=False, file=str(tmp_path / "output.txt")
    )
    action2 = Vals(vals={"payload": {"x": "Eureka!"}})
    action3 = All(include_processing_info=True, actions=[action2, action1])
    scheduler = Timely(interval=1)

    await add_action(base_url=base_url, action_name="foo", action=action3)
    await add_scheduler(base_url=base_url, scheduler_name="bar", scheduler=scheduler)
    await schedule_action(base_url=base_url, action_name="foo", scheduler_name="bar")

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(action1.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("Eureka!" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_execute_action(
    startup_and_shutdown_uvicorn, base_url, tmp_path, host, port
):
    await reset_dispatcher(base_url, str(tmp_path))

    server = Server(host=host, port=port, tags={"role": ["pivot"]})
    assert server.port == port
    assert server.host == host
    await add_server(base_url=base_url, server_name="test", server=server)
    file_append = file_x.FileAppend(
        # mode = "D",
        relative_to_output_dir=False,
        file=str(tmp_path / "output.txt"),
        payload={"hi": "pyrambium"},
    )
    info = sys_x.SysInfo()
    execute_action = disp_x.Exec(server_name="test", action_name="file_append")
    actions = All(actions=[info, execute_action])
    timely = Timely(interval=1)

    await add_action(base_url=base_url, action_name="file_append", action=file_append)
    await add_action(base_url=base_url, action_name="actions", action=actions)
    await add_scheduler(base_url=base_url, scheduler_name="timely", scheduler=timely)
    await schedule_action(
        base_url=base_url, action_name="actions", scheduler_name="timely"
    )
    await assert_scheduled_action_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(file_append.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("virtual_memory" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_execute_supplied_action(
    startup_and_shutdown_uvicorn, base_url, tmp_path, host, port
):
    await reset_dispatcher(base_url, str(tmp_path))

    server = Server(host=host, port=port, tags={"role": ["pivot"]})
    assert server.port == port
    assert server.host == host
    await add_server(base_url=base_url, server_name="test", server=server)
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

    await add_action(base_url=base_url, action_name="file_append", action=file_append)
    await add_action(base_url=base_url, action_name="actions", action=actions)
    await add_scheduler(base_url=base_url, scheduler_name="timely", scheduler=timely)
    await schedule_action(
        base_url=base_url, action_name="actions", scheduler_name="timely"
    )
    await assert_scheduled_action_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(file_append.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("virtual_memory" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_execute_action_key_tags(
    startup_and_shutdown_uvicorn, base_url, tmp_path, host, port
):
    await reset_dispatcher(base_url, str(tmp_path))

    server = Server(host=host, port=port, tags={"role": ["pivot"]})
    assert server.port == port
    assert server.host == host
    await add_server(base_url=base_url, server_name="test", server=server)
    file_append = file_x.FileAppend(
        # mode = "D",
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

    await add_action(base_url=base_url, action_name="file_append", action=file_append)
    await add_action(base_url=base_url, action_name="actions", action=actions)
    await add_scheduler(base_url=base_url, scheduler_name="timely", scheduler=timely)
    await schedule_action(
        base_url=base_url, action_name="actions", scheduler_name="timely"
    )
    await assert_scheduled_action_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(file_append.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("virtual_memory" in line for line in lines)


@pytest.mark.asyncio
async def test_file_append_execute_action_supplied_key_tags(
    startup_and_shutdown_uvicorn, base_url, tmp_path, host, port
):
    await reset_dispatcher(base_url, str(tmp_path))

    server = Server(host=host, port=port, tags={"role": ["pivot"]})
    assert server.port == port
    assert server.host == host
    await add_server(base_url=base_url, server_name="test", server=server)
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

    await add_action(base_url=base_url, action_name="file_append", action=file_append)
    await add_action(base_url=base_url, action_name="actions", action=actions)
    await add_scheduler(base_url=base_url, scheduler_name="timely", scheduler=timely)
    await schedule_action(
        base_url=base_url, action_name="actions", scheduler_name="timely"
    )
    await assert_scheduled_action_count(base_url=base_url, n=1)

    await run_and_stop_jobs(base_url=base_url, pause=2)
    lines = None
    with open(file_append.file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1
    assert any("virtual_memory" in line for line in lines)


# ==========================================
# helpers


async def get_action(base_url: str, action_name: str):
    """ make sure action exists and resolves properly """
    response = await get(base_url, path=f"/actions/{action_name}")
    assert response.status_code == 200, f"failed to get action ({action_name})"
    retrieved_action = resolve_action(response.json())
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))
    return retrieved_action


async def execute_action(base_url: str, action_name: str):
    """ make sure action exists and resolves properly """
    response = await get(base_url, path=f"/actions/{action_name}")
    assert response.status_code == 200, f"failed to get action ({action_name})"
    retrieved_action = resolve_action(response.json())
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))
    response = await get(base_url, path=f"/actions/{action_name}/execute")
    assert response.status_code == 200, f"failed to execute action ({action_name})"
    return resolve_rez(response.json())


async def execute_action_with_rez(base_url: str, action_name: str, rez: Rez):
    """ make sure action exists and resolves properly """
    response = await get(base_url, path=f"/actions/{action_name}")
    assert response.status_code == 200, f"failed to get action ({action_name})"
    retrieved_action = resolve_action(response.json())
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))
    response = await post(base_url, path=f"/actions/{action_name}/execute", data=rez)
    assert (
        response.status_code == 200
    ), f"failed to execute action ({action_name}) with rez ({rez}) with response ({response.json()})"
    return resolve_rez(response.json())


async def add_action(base_url: str, action_name: str, action: Action):
    """ add an action and confirm """
    response = await post(
        base_url=base_url, path=f"/actions/{action_name}", data=action
    )
    assert response.status_code == 200, f"failed to put action ({action_name})"
    response = await get(base_url, path=f"/actions/{action_name}")
    assert response.status_code == 200, f"failed to get action ({action_name})"
    retrieved_action = resolve_action(response.json())
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))


async def set_action(base_url: str, action_name: str, action: Action):
    """ set an action and confirm """
    response = await put(base_url=base_url, path=f"/actions/{action_name}", data=action)
    assert response.status_code == 200, f"failed to put action ({action_name})"
    response = await get(base_url, path=f"/actions/{action_name}")
    assert response.status_code == 200, f"failed to get action ({action_name})"
    retrieved_action = resolve_action(response.json())
    assert isinstance(retrieved_action, Action), str(type(retrieved_action))


async def get_scheduler(base_url: str, scheduler_name: str):
    """ make sure scheduler exists and resolves properly """
    response = await get(base_url, path=f"/schedulers/{scheduler_name}")
    assert response.status_code == 200, f"failed to get scheduler ({scheduler_name})"
    retrieved_scheduler = resolve_scheduler(response.json())
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))
    return retrieved_scheduler


async def add_scheduler(base_url: str, scheduler_name: str, scheduler: Scheduler):
    """ add a scheduler and confirm """
    response = await post(
        base_url=base_url, path=f"/schedulers/{scheduler_name}", data=scheduler
    )
    assert response.status_code == 200, f"failed to put scheduler ({scheduler_name})"
    response = await get(base_url, path=f"/schedulers/{scheduler_name}")
    assert response.status_code == 200, f"failed to get scheduler ({scheduler_name})"
    retrieved_scheduler = resolve_scheduler(response.json())
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))


async def set_scheduler(base_url: str, scheduler_name: str, scheduler: Scheduler):
    """ add a scheduler and confirm """
    response = await put(
        base_url=base_url, path=f"/schedulers/{scheduler_name}", data=scheduler
    )
    assert response.status_code == 200, f"failed to put scheduler ({scheduler_name})"
    response = await get(base_url, path=f"/schedulers/{scheduler_name}")
    assert response.status_code == 200, f"failed to get scheduler ({scheduler_name})"
    retrieved_scheduler = resolve_scheduler(response.json())
    assert isinstance(retrieved_scheduler, Scheduler), str(type(retrieved_scheduler))


async def unschedule_scheduler(base_url: str, scheduler_name: str):
    response = await get(
        base_url=base_url, path=f"/schedulers/{scheduler_name}/unschedule"
    )
    assert (
        response.status_code == 200
    ), f"failed to unschedule scheduler ({scheduler_name})"


async def schedule_action(base_url: str, scheduler_name: str, action_name: str):
    """ schedule an action """
    response = await get(
        base_url=base_url, path=f"/schedulers/{scheduler_name}/actions/{action_name}"
    )
    assert (
        response.status_code == 200
    ), f"failed to schedule action ({action_name}) using scheduler ({scheduler_name})"


async def get_program(base_url: str, program_name: str):
    """ make sure program exists and resolves properly """
    response = await get(base_url, path=f"/programs/{program_name}")
    assert response.status_code == 200, f"failed to get program ({program_name})"
    retrieved_program = resolve_program(response.json())
    assert isinstance(retrieved_program, Program), str(type(retrieved_program))
    return retrieved_program


async def add_program(base_url: str, program_name: str, program: Program):
    """ add a program and confirm """
    response = await post(
        base_url=base_url, path=f"/programs/{program_name}", data=program
    )
    assert response.status_code == 200, f"failed to post program ({program_name})"
    response = await get(base_url, path=f"/programs/{program_name}")
    assert response.status_code == 200, f"failed to get program ({program_name})"
    retrieved_program = resolve_program(response.json())
    assert isinstance(retrieved_program, Program), str(type(retrieved_program))


async def set_program(base_url: str, program_name: str, program: Action):
    """ set a program and confirm """
    response = await put(
        base_url=base_url, path=f"/programs/{program_name}", data=program
    )
    assert response.status_code == 200, f"failed to put program ({program_name})"
    response = await get(base_url, path=f"/programs/{program_name}")
    assert response.status_code == 200, f"failed to get program ({program_name})"
    retrieved_program = resolve_program(response.json())
    assert isinstance(retrieved_program, Program), str(type(retrieved_program))


async def schedule_program(base_url: str, program_name: str, start_stop: DateTime2):
    """ schedule a program """
    response = await post(
        base_url=base_url, path=f"/programs/{program_name}/schedule", data=start_stop
    )
    assert response.status_code == 200, f"failed to schedule program ({program_name})"


async def unschedule_program(base_url: str, program_name: str):
    """ schedule a program """
    response = await get(base_url=base_url, path=f"/programs/{program_name}/unschedule")
    assert response.status_code == 200, f"failed to unschedule program ({program_name})"


async def delete_program(base_url: str, program_name: str):
    """ delete a program """
    response = await delete(base_url=base_url, path=f"/programs/{program_name}")
    assert response.status_code == 200, f"failed to delete program ({program_name})"


async def add_server(base_url: str, server_name: str, server: Server):
    """ add a server and confirm """
    response = await post(
        base_url=base_url, path=f"/servers/{server_name}", data=server
    )
    assert response.status_code == 200, f"failed to post server ({server_name})"
    response = await get(base_url, path=f"/servers/{server_name}")
    assert response.status_code == 200, f"failed to get server ({server_name})"
    retrieved = resolve_server(response.json())
    assert isinstance(retrieved, Server), str(type(retrieved))


async def set_server(base_url: str, server_name: str, server: Server):
    """ set a server and confirm """
    response = await put(base_url=base_url, path=f"/servers/{server_name}", data=server)
    assert response.status_code == 200, f"failed to put server ({server_name})"
    response = await get(base_url, path=f"/servers/{server_name}")
    assert response.status_code == 200, f"failed to get server ({server_name})"
    retrieved = resolve_server(response.json())
    assert isinstance(retrieved, Server), str(type(retrieved))


async def delete_server(base_url: str, server_name: str):
    """ delete a server """
    response = await delete(base_url=base_url, path=f"/servers/{server_name}")
    assert response.status_code == 200, f"failed to delete server ({server_name})"


async def defer_action(
    base_url: str, scheduler_name: str, action_name: str, wait_until: DateTime
):
    """ defer an action """
    response = await post(
        base_url=base_url,
        path=f"/schedulers/{scheduler_name}/actions/{action_name}/defer",
        data=wait_until,
    )
    assert (
        response.status_code == 200
    ), f"failed to defer action ({action_name}) using scheduler ({scheduler_name})"


async def expire_action(
    base_url: str, scheduler_name: str, action_name: str, expire_on: DateTime
):
    """ expire an action """
    response = await post(
        base_url=base_url,
        path=f"/schedulers/{scheduler_name}/actions/{action_name}/expire",
        data=expire_on,
    )
    assert (
        response.status_code == 200
    ), f"failed to expire action ({action_name}) using scheduler ({scheduler_name})"


async def load_dispatcher(base_url: str):
    """ return the saved dispatcher """
    response = await get(base_url=base_url, path="/dispatcher/load")
    assert (
        response.status_code == 200
    ), f"failed to load the dispatcher ({response.json()})"
    retrieved_dispatcher = Dispatcher.resolve(response.json())
    assert isinstance(retrieved_dispatcher, Dispatcher), str(type(retrieved_dispatcher))
    return retrieved_dispatcher


async def get_saved_dir(base_url: str):
    """ return saved_dir """
    response = await get(base_url=base_url, path="/dispatcher/saved_dir")
    assert (
        response.status_code == 200
    ), f"failed to retrieve saved_dir ({response.json()})"
    saved_dir = response.json()
    return saved_dir


async def replace_dispatcher(base_url: str, replacement: Dispatcher):
    """
    replace a dispatcher
    """
    response = await put(
        base_url=base_url, path="/dispatcher/replace", data=replacement
    )
    assert (
        response.status_code == 200
    ), f"failed to replace the dispatcher ({response.json()}"


async def unschedule_all(base_url: str):
    """
    unschedule all schedulers and actions
    """
    response = await get(base_url=base_url, path="/schedulers/unschedule_all")
    assert response.status_code == 200, "failed to unschedule all schedulers"


async def clear_all_scheduling(base_url: str):
    """
    clear all scheduling
    """
    response = await get(base_url=base_url, path="/schedulers/clear_scheduling")
    assert response.status_code == 200, "failed to clear all scheduling"


async def reschedule_all(base_url: str):
    """
    reschedule all schedulers and actions
    """
    response = await get(base_url=base_url, path="/schedulers/reschedule_all")
    assert response.status_code == 200, "failed to reschedule all schedulers"


async def reset_dispatcher(base_url: str, tmp_dir: str):
    """
    usage: reset_dispatcher(base_url, str(tmp_path))
    """

    # set saved_dir to fixture, tmp_path (see usage)
    saved_dir = FilePathe(path=tmp_dir)
    response = await put(
        base_url=base_url, path="/dispatcher/saved_dir", data=saved_dir
    )
    assert response.status_code == 200, "failed to set saved_dir"
    response = await get(base_url=base_url, path="/dispatcher/saved_dir")
    assert response.status_code == 200, "failed to get saved_dir"
    saved_saved_dir = resolve_file_pathe(response.json())
    assert saved_saved_dir == saved_dir

    # empty the dispatcher and stop the jobs if they're running
    # for uvicorn tests to run in a bunch, these objects need to be 'reset' since
    # evidently the app is shared during the running of the tests
    response = await get(base_url=base_url, path="/dispatcher/clear")
    assert response.status_code == 200, "failed to get clear dispatcher"
    response = await get(base_url=base_url, path="/jobs/stop")  # likely already stopped


async def assert_job_count(base_url: str, n: int):
    response = await get(base_url, "/jobs/count")
    assert response.status_code == 200, "failed to retrieve job count"
    job_count = int(response.json()["job_count"])
    assert job_count == n, f"expected a job count of ({n}); instead got ({job_count})"


async def assert_scheduled_action_count(base_url: str, n: int):
    response = await get(base_url, "/schedulers/action_count")
    assert response.status_code == 200, "failed to retrieve action count"
    action_count = int(response.json()["action_count"])
    assert (
        action_count == n
    ), f"expected an action count of ({n}); instead got ({action_count})"


async def assert_deferred_action_count(base_url: str, n: int):
    response = await get(base_url, "/schedulers/deferred_action_count")
    assert response.status_code == 200, "failed to retrieve deferred action count"
    deferred_action_count = int(response.json()["deferred_action_count"])
    assert (
        deferred_action_count == n
    ), f"expected an deferred action count of ({n}); instead got ({deferred_action_count})"


async def assert_expiring_action_count(base_url: str, n: int):
    response = await get(base_url, "/schedulers/expiring_action_count")
    assert response.status_code == 200, "failed to retrieve expiring action count"
    expiring_action_count = int(response.json()["expiring_action_count"])
    assert (
        expiring_action_count == n
    ), f"expected an expiring action count of ({n}); instead got ({expiring_action_count})"


async def assert_deferred_program_count(base_url: str, n: int):
    response = await get(base_url, "/programs/deferred_program_count")
    assert response.status_code == 200, "failed to retrieve deferred program count"
    deferred_program_count = int(response.json()["deferred_program_count"])
    assert (
        deferred_program_count == n
    ), f"expected an deferred program count of ({n}); instead got ({deferred_program_count})"


async def run_and_stop_jobs(base_url: str, pause: int):
    response = await get(base_url, "/jobs/run")
    assert response.status_code == 200, "failed to run jobs"
    time.sleep(pause)
    response = await get(base_url, "/jobs/stop")
    assert response.status_code == 200, "failed to stop jobs"


# verbs
async def get(base_url: str, path: str):
    async with AsyncClient(base_url=base_url) as ac:
        result = await ac.get(url=path)
        return result


async def put(base_url: str, path: str, data: BaseModel):
    async with AsyncClient(base_url=base_url) as ac:
        return await ac.put(url=path, data=data.json())


async def post(base_url: str, path: str, data: BaseModel):
    async with AsyncClient(base_url=base_url) as ac:
        return await ac.post(url=path, data=data.json())


async def post_dict(base_url: str, path: str, data: dict):
    async with AsyncClient(base_url=base_url) as ac:
        return await ac.post(url=path, data=json.dumps(data))


async def delete(base_url: str, path: str):
    async with AsyncClient(base_url=base_url) as ac:
        return await ac.delete(url=path)
