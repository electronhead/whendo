from pydantic import BaseModel
import requests
from whendo.core.action import Action
from whendo.core.scheduler import Scheduler
from whendo.core.resolver import resolve_action, resolve_scheduler, resolve_file_pathe
from whendo.core.util import FilePathe
from whendo.core.dispatcher import Dispatcher

class Client(BaseModel):
    host:str='127.0.0.1'
    port:int=8000

    # /dispatcher
    def load_dispatcher(self):
        return Dispatcher.resolve(self.get(f"/dispatcher/load"))
    def save_dispatcher(self):
        return self.get("/dispatcher/save")
    def clear_dispatcher(self):
        return self.get("/dispatcher/clear")
    def load_dispatcher_from_name(self, name:str):
        return Dispatcher.resolve(self.get(f"/dispatcher/load_from_name/{name}"))
    def save_data_to_name(self, name:str):
        return self.get(f"/dispatcher/save_to_name/{name}")
    def get_saved_dir(self):
        return resolve_file_pathe(self.get("/dispatcher/saved_dir"))
    def set_saved_dir(self, saved_dir:FilePathe):
        return self.put("/dispatcher/saved_dir", saved_dir)

    # /actions
    def get_action(self, action_name:str):
        return resolve_action(self.get(f"/actions/{action_name}"))
    def add_action(self, action_name:str, action:Action):
        return self.post(f"/actions/{action_name}", action)
    def set_action(self, action_name:str, action:Action):
        return self.put(f"/actions/{action_name}", action)
    def delete_action(self, action_name:str):
        return self.delete(f"/actions/{action_name}")
    def execute_action(self, action_name:str):
        return self.get(f"/actions/{action_name}/execute")
    def unschedule_action(self, action_name:str):
        return self.get(f"/actions/{action_name}/unschedule")
    def reschedule_action(self, action_name:str):
        return self.get(f"/actions/{action_name}/reschedule")

    # /schedulers
    def schedule_action(self, scheduler_name:str, action_name:str):
        return self.get(f"/schedulers/{scheduler_name}/actions/{action_name}")
    def get_scheduler(self, scheduler_name:str):
        return resolve_scheduler(self.get(f"/schedulers/{scheduler_name}"))
    def add_scheduler(self, scheduler_name:str, scheduler:Scheduler):
        return self.post(f"/schedulers/{scheduler_name}", scheduler)
    def set_scheduler(self, scheduler_name:str, scheduler:Scheduler):
        return self.put(f"/schedulers/{scheduler_name}", scheduler)
    def delete_scheduler(self, scheduler_name:str):
        return self.delete(f"/schedulers/{scheduler_name}")
    def unschedule_scheduler(self, scheduler_name:str):
        return self.get(f"/schedulers/{scheduler_name}/unschedule")
    def reschedule_all_schedulers(self):
        return self.get(f"/schedulers/reschedule_all")
    def execute_scheduler_actions(self, scheduler_name:str):
        return self.get(f"/schedulers/{scheduler_name}/execute")

    # /jobs
    def run_jobs(self):
        return self.get(f"/jobs/run")
    def stop_jobs(self):
        return self.get(f"/jobs/stop")
    def jobs_are_running(self):
        return self.get(f"/jobs/are_running")
    def job_count(self):
        return self.get(f"/jobs/count")
    def clear_jobs(self):
        return self.get(f"/jobs/clear")

    # verbs
    def get(self, path:str, data=None):
        response = requests.get(self.cmd(path), data)
        assert response.status_code == 200, response.text
        return response.json()
    def put(self, path:str, data:BaseModel):
        response = requests.put(self.cmd(path), data.json())
        assert response.status_code == 200, response.text
        return response.json()
    def post(self, path:str, data:BaseModel):
        response = requests.post(self.cmd(path), data.json())
        assert response.status_code == 200, response.text
        return response.json()
    def delete(self, path:str):
        response = requests.delete(self.cmd(path))
        assert response.status_code == 200, response.text
        return response.json()
    def cmd(self, path:str):
        return f"http://{self.host}:{self.port}{path}"
