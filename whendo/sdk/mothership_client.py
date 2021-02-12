from pydantic import BaseModel
import requests
from whendo.core.action import Action
from whendo.core.scheduler import Scheduler
from whendo.core.resolver import resolve_action, resolve_scheduler, resolve_file_pathe
from whendo.core.util import resolve_instance, FilePathe
from whendo.core.mothership import Mothership

class MothershipClient(BaseModel):
    ip_addr:str
    port:int=8000

    # /mothership
    def load_mothership(self):
        return Mothership.resolve(self.get(f"/mothership/load"))
    def save_mothership(self):
        return self.get("/mothership/save")
    def clear_mothership(self):
        return self.get("/mothership/clear")
    def load_mothership_from_name(self, name:str):
        return Mothership.resolve(self.get(f"/mothership/load_from_name/{name}"))
    def save_mothership_to_name(self, name:str):
        return self.get(f"/mothership/save_to_name/{name}")
    def get_saved_dir(self):
        return resolve_file_pathe(self.get("/mothership/saved_dir"))
    def set_saved_dir(self, saved_dir:FilePathe):
        return self.put("/mothership/saved_dir", saved_dir)

    # /actions
    def get_action(self, action_name:str):
        return resolve_action(self.get(f"/actions/{action_name}"))
    def add_action(self, action_name:str, action:Action):
        return self.put(f"/actions/{action_name}", action)
    def remove_action(self, action_name:str):
        return self.delete(f"/actions/{action_name}")
    def update_action(self, action_name:str, dictionary:dict):
        return self.patch(f"/actions/{action_name}", dictionary)
    def execute_action(self, action_name:str):
        return self.get(f"/actions/{action_name}/execute")
    def unschedule_action(self, action_name:str):
        return self.get(f"/actions/{action_name}/unschedule")

    # /schedulers
    def schedule_action(self, scheduler_name:str, action_name:str):
        return self.get(f"/schedulers/{scheduler_name}/actions/{action_name}")
    def get_scheduler(self, scheduler_name:str):
        return resolve_scheduler(self.get(f"/schedulers/{scheduler_name}"))
    def add_scheduler(self, scheduler_name:str, scheduler:Scheduler):
        return self.put(f"/schedulers/{scheduler_name}", scheduler)
    def remove_scheduler(self, scheduler_name:str):
        return self.delete(f"/schedulers/{scheduler_name}")
    def update_scheduler(self, scheduler_name:str, dictionary:dict):
        return self.patch(f"/schedulers/{scheduler_name}", dictionary)
    def execute_scheduler_actions(self, scheduler_name:str):
        return self.get(f"/schedulers/{scheduler_name}/execute")
    def unschedule_scheduler(self, scheduler_name:str):
        return self.delete(f"/schedulers/{scheduler_name}/unschedule")
    def reschedule_all_schedulers(self):
        return self.delete(f"/schedulers/reschedule_all")

    # /jobs
    def start_scheduled_jobs(self):
        return self.get(f"/jobs/start")
    def stop_scheduled_jobs(self):
        return self.get(f"/jobs/stop")
    def job_count(self):
        return self.get(f"/jobs/count")

    # verbs
    def get(self, path:str, data=None):
        response = requests.get(self.cmd(path), data)
        return response.json()
    def put(self, path:str, data:BaseModel):
        response = requests.put(self.cmd(path), data.json())
        return response.json()
    def post(self, path:str, data:BaseModel):
        response = requests.post(self.cmd(path), data.json())
        return response.json()
    def patch(self, path:str, data:dict):
        response = requests.patch(self.cmd(path), data)
        return response.json()
    def delete(self, path:str):
        response = requests.delete(self.cmd(path))
        return response.json()
    def cmd(self, path:str):
        return f"http://{self.ip_addr}:{self.port}{path}"
