from pydantic import BaseModel, PrivateAttr
import requests
import logging
from typing import Optional
from whendo.core.action import Action, ActionRez, Rez, RezDict
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
from whendo.core.util import FilePathe, DateTime, Http, DateTime2, Rez
from whendo.core.dispatcher import Dispatcher
from whendo.core.program import Program

logger = logging.getLogger(__name__)


class Client(BaseModel):
    host: str
    port: int
    client_used: bool = False
    http_instance: Optional[Http] = None

    def get_host(self):
        return self.host

    def http(self):
        """
        Cache the Http object.
        """
        if self.http_instance == None:
            self.http_instance = Http(host=self.host, port=self.port)
        return self.http_instance

    # /dispatcher
    def load_dispatcher(self):
        return Dispatcher.resolve(self.http().get(f"/dispatcher/load"))

    def save_dispatcher(self):
        return self.http().get("/dispatcher/save")

    def clear_dispatcher(self):
        return self.http().get("/dispatcher/clear")

    def load_dispatcher_from_name(self, name: str):
        return Dispatcher.resolve(self.http().get(f"/dispatcher/load_from_name/{name}"))

    def save_data_to_name(self, name: str):
        return self.http().get(f"/dispatcher/save_to_name/{name}")

    def get_saved_dir(self):
        return resolve_file_pathe(self.http().get("/dispatcher/saved_dir"))

    def set_saved_dir(self, saved_dir: FilePathe):
        return self.http().put("/dispatcher/saved_dir", saved_dir)

    def replace_dispatcher(self, replacement: Dispatcher):
        return self.http().put("/dispatcher/replace", replacement)

    def describe_all(self):
        return self.http().get("/dispatcher/describe_all")

    # /execution

    def execute_supplied_action(self, supplied_action: Action):
        response = self.http().post(f"/execution", supplied_action)
        return resolve_rez(response)

    def execute_supplied_action_with_rez(self, supplied_action: Action, rez: Rez):
        # action_rez = ActionRez(action=supplied_action, rez=rez)
        # response = self.http().post(f"/execution/with_rez", action_rez)
        supplied_action.complete_fields(rez=rez)
        response = self.http().post(f"/execution", supplied_action)
        return resolve_rez(response)

    # /actions
    def get_action(self, action_name: str):
        return resolve_action(self.http().get(f"/actions/{action_name}"))

    def describe_action(self, action_name: str):
        return self.http().get(f"/actions/{action_name}/describe")

    def add_action(self, action_name: str, action: Action):
        return self.http().post(f"/actions/{action_name}", action)

    def set_action(self, action_name: str, action: Action):
        return self.http().put(f"/actions/{action_name}", action)

    def delete_action(self, action_name: str):
        return self.http().delete(f"/actions/{action_name}")

    def execute_action(self, action_name: str):
        return resolve_rez(self.http().get(f"/actions/{action_name}/execute"))

    def execute_action_with_rez(self, action_name: str, rez: Rez):
        return resolve_rez(self.http().post(f"/actions/{action_name}/execute", rez))

    # /schedulers

    def schedule_action(self, scheduler_name: str, action_name: str):
        return self.http().get(f"/schedulers/{scheduler_name}/actions/{action_name}")

    def get_scheduler(self, scheduler_name: str):
        return resolve_scheduler(self.http().get(f"/schedulers/{scheduler_name}"))

    def describe_scheduler(self, scheduler_name: str):
        return self.http().get(f"/schedulers/{scheduler_name}/describe")

    def add_scheduler(self, scheduler_name: str, scheduler: Scheduler):
        return self.http().post(f"/schedulers/{scheduler_name}", scheduler)

    def set_scheduler(self, scheduler_name: str, scheduler: Scheduler):
        return self.http().put(f"/schedulers/{scheduler_name}", scheduler)

    def delete_scheduler(self, scheduler_name: str):
        return self.http().delete(f"/schedulers/{scheduler_name}")

    def unschedule_scheduler(self, scheduler_name: str):
        return self.http().get(f"/schedulers/{scheduler_name}/unschedule")

    def unschedule_all_schedulers(self):
        return self.http().get(f"/schedulers/unschedule_all")

    def unschedule_scheduler_action(self, scheduler_name: str, action_name: str):
        return self.http().get(
            f"/schedulers/{scheduler_name}/actions/{action_name}/unschedule"
        )

    def rescheduler_scheduler(self, scheduler_name: str):
        return self.http().get(f"/schedulers/{scheduler_name}/reschedule")

    def reschedule_all_schedulers(self):
        return self.http().get(f"/schedulers/reschedule_all")

    def scheduled_action_count(self):
        return self.http().get("/schedulers/action_count")

    def clear_all_scheduling(self):
        return self.http().get("/schedulers/clear_scheduling")

    # programs
    def get_program(self, program_name: str):
        return resolve_program(self.http().get(f"/programs/{program_name}"))

    def describe_program(self, program_name: str):
        return self.http().get(f"/programs/{program_name}/describe")

    def add_program(self, program_name: str, program: Program):
        return self.http().post(f"/programs/{program_name}", program)

    def set_program(self, program_name: str, program: Program):
        return self.http().put(f"/programs/{program_name}", program)

    def delete_program(self, program_name: str):
        return self.http().delete(f"/programs/{program_name}")

    def schedule_program(self, program_name: str, start_stop: DateTime2):
        return self.http().post(f"/programs/{program_name}/schedule", start_stop)

    def unschedule_program(self, program_name: str):
        return self.http().get(f"/programs/{program_name}/unschedule")

    def clear_deferred_programs(self):
        return self.http().get(f"/programs/clear_deferred_programs")

    def deferred_program_count(self):
        return self.http().get(f"/programs/deferred_program_count")

    # servers

    def get_server(self, server_name: str):
        return resolve_server(self.http().get(f"/servers/{server_name}"))

    def get_servers(self, server_name: str):
        servers = self.http().get(f"/servers")
        return {name: resolve_server(servers[name]) for name in servers}

    def describe_server(self, server_name: str):
        return self.http().get(f"/servers/{server_name}/describe")

    def add_server(self, server_name: str, server: Server):
        return self.http().post(f"/servers/{server_name}", server)

    def set_server(self, server_name: str, server: Server):
        return self.http().put(f"/servers/{server_name}", server)

    def delete_server(self, server_name: str):
        return self.http().delete(f"/servers/{server_name}")

    def get_server_tags(self, server_name: str):
        return self.http().get(f"/servers/{server_name}/get_tags")

    def get_servers_by_tags(self, server_name: str, key_tags: dict):
        return self.http().post_dict(f"/servers/by_tags", key_tags)

    def execute_on_server(self, server_name: str, action_name: str):
        return resolve_rez(
            self.http().get(f"/servers/{server_name}/actions/{action_name}/execute")
        )

    def execute_on_server_with_rez(self, server_name: str, action_name: str, rez: Rez):
        return resolve_rez(
            self.http().post(
                f"/servers/{server_name}/actions/{action_name}/execute", rez
            )
        )

    def execute_on_servers(self, mode: str, action_name: str, key_tags: dict):
        return self.http().post_dict(
            f"/servers/by_tags/{mode}/actions/{action_name}/execute", key_tags
        )

    def execute_on_servers_with_rez(
        self, mode: str, action_name: str, key_tags: dict, rez: Rez
    ):
        rez_dict = RezDict(r=rez, d=key_tags)
        return self.http().post(
            f"/servers/by_tags/{mode}/actions/{action_name}/execute_with_rez",
            rez_dict,
        )

    # deferrals and expirations
    def defer_action(self, scheduler_name: str, action_name: str, wait_until: DateTime):
        return self.http().post(
            f"/schedulers/{scheduler_name}/actions/{action_name}/defer", wait_until
        )

    def clear_deferred_actions(self):
        return self.http().get(f"/schedulers/clear_deferred_actions")

    def deferred_action_count(self):
        return self.http().get("/schedulers/deferred_action_count")

    def expire_action(self, scheduler_name: str, action_name: str, expire_on: DateTime):
        return self.http().post(
            f"/schedulers/{scheduler_name}/actions/{action_name}/expire", expire_on
        )

    def clear_expiring_actions(self):
        return self.http().get(f"/schedulers/clear_expiring_actions")

    def expiring_action_count(self):
        return self.http().get("/schedulers/expiring_action_count")

    # /jobs
    def run_jobs(self):
        return self.http().get(f"/jobs/run")

    def stop_jobs(self):
        return self.http().get(f"/jobs/stop")

    def jobs_are_running(self):
        return self.http().get(f"/jobs/are_running")

    def job_count(self):
        return self.http().get(f"/jobs/count")

    def clear_jobs(self):
        return self.http().get(f"/jobs/clear")
