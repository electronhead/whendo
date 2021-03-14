from pydantic import BaseModel, PrivateAttr
import requests
import logging
from typing import Optional
from whendo.core.action import Action
from whendo.core.scheduler import Scheduler
from whendo.core.resolver import (
    resolve_action,
    resolve_scheduler,
    resolve_file_pathe,
    resolve_program,
)
from whendo.core.util import FilePathe, DateTime, Http, DateTime2
from whendo.core.dispatcher import Dispatcher
from whendo.core.program import Program

default_host = "127.0.0.1"
default_port = 8000

logger = logging.getLogger(__name__)


class Client(BaseModel):
    host: str = default_host
    port: int = default_port
    client_used: bool = False

    # hidden private field
    _http: Http = PrivateAttr(default_factory=Http)

    def http(self):
        """
        Cache the Http object.
        """
        if not self.client_used:
            self._http = Http(host=self.host, post=self.port)
            self.client_used = True
        return self._http

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
        return self.http().put(f"/execution", supplied_action)

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
        return self.http().get(f"/actions/{action_name}/execute")

    def unschedule_action(self, action_name: str):
        return self.http().get(f"/actions/{action_name}/unschedule")

    def reschedule_action(self, action_name: str):
        return self.http().get(f"/actions/{action_name}/reschedule")

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

    def unschedule_scheduler_action(self, scheduler_name: str, action_name: str):
        return self.http().get(
            f"/schedulers/{scheduler_name}/actions/{action_name}/unschedule"
        )

    def reschedule_all_schedulers(self):
        return self.http().get(f"/schedulers/reschedule_all")

    def execute_scheduler_actions(self, scheduler_name: str):
        return self.http().get(f"/schedulers/{scheduler_name}/execute")

    def scheduled_action_count(self):
        return self.http().get("/schedulers/action_count")

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

    def schedule_program(self, program_name: str, datetime2: DateTime2):
        return self.http().post(f"/programs/{program_name}/schedule", datetime2)

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

    def clear_expired_actions(self):
        return self.http().get(f"/schedulers/clear_expired_actions")

    def expired_action_count(self):
        return self.http().get("/schedulers/expired_action_count")

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
