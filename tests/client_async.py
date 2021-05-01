from pydantic import BaseModel
from httpx import AsyncClient
import json
from whendo.core.action import Action, ActionRez, RezDict
from whendo.core.scheduler import Scheduler
from whendo.core.server import Server
from whendo.core.resolver import (
    resolve_action,
    resolve_scheduler,
    resolve_file_pathe,
    resolve_program,
    resolve_server,
    resolve_rez,
)
from whendo.core.util import FilePathe, DateTime, DateTime2, Rez
from whendo.core.dispatcher import Dispatcher
from whendo.core.program import Program


class ClientAsync(BaseModel):
    """
    This class is very similar to Client, except that the methods
    that typically return BaseModel objects will return supplied
    dictionaries if resolution fails.
    """

    host: str
    port: int

    # /dispatcher
    async def load_dispatcher(self):
        return Dispatcher.resolve(await self.get_as_json(f"/dispatcher/load"))

    async def save_dispatcher(self):
        return await self.get("/dispatcher/save")

    async def clear_dispatcher(self):
        return await self.get("/dispatcher/clear")

    async def load_dispatcher_from_name(self, name: str):
        return Dispatcher.resolve(
            await self.get_as_json(f"/dispatcher/load_from_name/{name}")
        )

    async def save_data_to_name(self, name: str):
        return await self.get(f"/dispatcher/save_to_name/{name}")

    async def get_saved_dir(self):
        return resolve_file_pathe(
            await self.get_as_json("/dispatcher/saved_dir"), check_for_found_class=False
        )

    async def set_saved_dir(self, saved_dir: FilePathe):
        return await self.put("/dispatcher/saved_dir", saved_dir)

    async def replace_dispatcher(self, replacement: Dispatcher):
        return await self.put("/dispatcher/replace", replacement)

    async def describe_all(self):
        return await self.get("/dispatcher/describe_all")

    # /execution
    async def execute_supplied_action(self, supplied_action: Action):
        response = await self.post("/execution", supplied_action)
        return resolve_rez(response.json())

    async def execute_supplied_action_with_rez(self, supplied_action: Action, rez: Rez):
        # action_rez = ActionRez(action=supplied_action, rez=rez)
        # response = await self.post("/execution/with_rez", action_rez)
        supplied_action.complete_fields(rez=rez)
        response = await self.post("/execution", supplied_action)
        return resolve_rez(response.json())

    # /actions
    async def get_action(self, action_name: str):
        return resolve_action(
            await self.get_as_json(f"/actions/{action_name}"),
            check_for_found_class=False,
        )

    async def add_action(self, action_name: str, action: Action):
        return await self.post(f"/actions/{action_name}", action)

    async def set_action(self, action_name: str, action: Action):
        return await self.put(f"/actions/{action_name}", action)

    async def delete_action(self, action_name: str):
        return await self.delete(f"/actions/{action_name}")

    async def execute_action(self, action_name: str):
        return await self.get(f"/actions/{action_name}/execute")

    async def execute_action_with_rez(self, action_name: str, rez: Rez):
        return await self.post(f"/actions/{action_name}/execute", rez)

    # /schedulers
    async def schedule_action(self, scheduler_name: str, action_name: str):
        return await self.get(f"/schedulers/{scheduler_name}/actions/{action_name}")

    async def get_scheduler(self, scheduler_name: str):
        return resolve_scheduler(
            await self.get_as_json(f"/schedulers/{scheduler_name}"),
            check_for_found_class=False,
        )

    async def describe_scheduler(self, scheduler_name: str):
        return await self.get(f"/schedulers/{scheduler_name}/describe")

    async def add_scheduler(self, scheduler_name: str, scheduler: Scheduler):
        return await self.post(f"/schedulers/{scheduler_name}", scheduler)

    async def set_scheduler(self, scheduler_name: str, scheduler: Scheduler):
        return await self.put(f"/schedulers/{scheduler_name}", scheduler)

    async def delete_scheduler(self, scheduler_name: str):
        return await self.delete(f"/schedulers/{scheduler_name}")

    async def unschedule_scheduler(self, scheduler_name: str):
        return await self.get(f"/schedulers/{scheduler_name}/unschedule")

    async def unschedule_all_schedulers(self):
        return await self.get(f"/schedulers/unschedule_all")

    async def reschedule_all_schedulers(self):
        return await self.get(f"/schedulers/reschedule_all")

    async def execute_scheduled_actions(self, scheduler_name: str):
        return await self.get(f"/schedulers/{scheduler_name}/execute")

    async def scheduled_action_count(self):
        return await self.get("/schedulers/action_count")

    async def clear_all_scheduling(self):
        return await self.get("/schedulers/clear_scheduling")

    # programs
    async def get_program(self, program_name: str):
        return resolve_program(
            await self.get_as_json(f"/programs/{program_name}"),
            check_for_found_class=False,
        )

    async def add_program(self, program_name: str, program: Program):
        return await self.post(f"/programs/{program_name}", program)

    async def set_program(self, program_name: str, program: Program):
        return await self.put(f"/programs/{program_name}", program)

    async def delete_program(self, program_name: str):
        return await self.delete(f"/programs/{program_name}")

    async def schedule_program(self, program_name: str, start_stop: DateTime2):
        return await self.post(f"/programs/{program_name}/schedule", start_stop)

    async def unschedule_program(self, program_name: str):
        return await self.get(f"/programs/{program_name}/unschedule")

    async def clear_deferred_programs(self):
        return await self.get(f"/programs/clear_deferred_programs")

    async def deferred_program_count(self):
        return await self.get(f"/programs/deferred_program_count")

    # servers

    async def get_server(self, server_name: str):
        return resolve_server(
            await self.get_as_json(f"/servers/{server_name}"),
            check_for_found_class=False,
        )

    async def get_servers(self):
        servers = await self.get(f"/servers")
        return {
            name: resolve_server(servers[name], check_for_found_class=False)
            for name in servers
        }

    async def describe_server(self, server_name: str):
        return await self.get(f"/servers/{server_name}/describe")

    async def add_server(self, server_name: str, server: Server):
        return await self.post(f"/servers/{server_name}", server)

    async def set_server(self, server_name: str, server: Server):
        return await self.put(f"/servers/{server_name}", server)

    async def delete_server(self, server_name: str):
        return await self.delete(f"/servers/{server_name}")

    async def get_server_tags(self, server_name: str):
        return await self.get(f"/servers/{server_name}/get_tags")

    async def get_servers_by_tags(self, server_name: str, key_tags: dict):
        return await self.post_dict(f"/servers/by_tags", key_tags)

    async def execute_on_server(self, server_name: str, action_name: str):
        return resolve_rez(
            await self.get(f"/servers/{server_name}/actions/{action_name}/execute")
        )

    async def execute_on_server_with_rez(
        self, server_name: str, action_name: str, rez: Rez
    ):
        return resolve_rez(
            await self.post(
                f"/servers/{server_name}/actions/{action_name}/execute", rez
            )
        )

    async def execute_on_servers(self, mode: str, action_name: str, key_tags: dict):
        return await self.post_dict(
            f"/servers/by_tags/{mode}/actions/{action_name}/execute", key_tags
        )

    async def execute_on_servers_with_rez(
        self, mode: str, action_name: str, key_tags: dict, rez: Rez
    ):
        rez_dict = RezDict(r=rez, d=key_tags)
        return await self.post(
            f"/servers/by_tags/{mode}/actions/{action_name}/execute_with_rez",
            rez_dict,
        )

    # deferrals and expirations
    async def defer_action(
        self, scheduler_name: str, action_name: str, wait_until: DateTime
    ):
        return await self.post(
            f"/schedulers/{scheduler_name}/actions/{action_name}/defer", wait_until
        )

    async def clear_deferred_actions(self):
        return await self.get(f"/schedulers/clear_deferred_actions")

    async def deferred_action_count(self):
        return await self.get("/schedulers/deferred_action_count")

    async def expire_action(
        self, scheduler_name: str, action_name: str, expire_on: DateTime
    ):
        return await self.post(
            f"/schedulers/{scheduler_name}/actions/{action_name}/expire", expire_on
        )

    async def clear_expiring_actions(self):
        return await self.get(f"/schedulers/clear_expiring_actions")

    async def expiring_action_count(self):
        return await self.get("/schedulers/expiring_action_count")

    # /jobs
    async def run_jobs(self):
        return await self.get(f"/jobs/run")

    async def stop_jobs(self):
        return await self.get(f"/jobs/stop")

    async def jobs_are_running(self):
        return await self.get(f"/jobs/are_running")

    async def job_count(self):
        return await self.get(f"/jobs/count")

    async def clear_jobs(self):
        return await self.get(f"/jobs/clear")

    # verbs
    async def get(self, path: str):
        async with AsyncClient(base_url=self.base_url()) as ac:
            return await ac.get(url=path)

    async def get_as_json(self, path: str):
        async with AsyncClient(base_url=self.base_url()) as ac:
            response = await ac.get(url=path)
            return response.json()

    async def put(self, path: str, data: BaseModel):
        async with AsyncClient(base_url=self.base_url()) as ac:
            return await ac.put(url=path, data=data.json())

    async def post(self, path: str, data: BaseModel):
        async with AsyncClient(base_url=self.base_url()) as ac:
            return await ac.post(url=path, data=data.json())

    async def post_dict(self, path: str, data: dict):
        async with AsyncClient(base_url=self.base_url()) as ac:
            return await ac.post(url=path, data=json.dumps(data))

    async def delete(self, path: str):
        async with AsyncClient(base_url=self.base_url()) as ac:
            return await ac.delete(url=path)

    def base_url(self):
        return f"http://{self.host}:{self.port}"
