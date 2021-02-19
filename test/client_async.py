from pydantic import BaseModel
from httpx import AsyncClient
from whendo.core.action import Action
from whendo.core.scheduler import Scheduler
from whendo.core.resolver import resolve_action, resolve_scheduler, resolve_file_pathe
from whendo.core.util import FilePathe
from whendo.core.dispatcher import Dispatcher

class ClientAsync(BaseModel):
    """
    This class is very similar to Client, except that the methods
    that typically return BaseModel objects will return supplied
    dictionaries if resolution fails. 
    """
    host:str='127.0.0.1'
    port:int=8000

    # /dispatcher
    async def load_dispatcher(self):
        return Dispatcher.resolve(await self.get_as_json(f"/dispatcher/load"))
    async def save_dispatcher(self):
        return await self.get("/dispatcher/save")
    async def clear_dispatcher(self):
        return await self.get("/dispatcher/clear")
    async def load_dispatcher_from_name(self, name:str):
        return Dispatcher.resolve(await self.get_as_json(f"/dispatcher/load_from_name/{name}"))
    async def save_data_to_name(self, name:str):
        return await self.get(f"/dispatcher/save_to_name/{name}")
    async def get_saved_dir(self):
        return resolve_file_pathe(await self.get_as_json("/dispatcher/saved_dir"), check_for_found_class=False)
    async def set_saved_dir(self, saved_dir:FilePathe):
        return await self.put("/dispatcher/saved_dir", saved_dir)

    # /actions
    async def get_action(self, action_name:str):
        return resolve_action(await self.get_as_json(f"/actions/{action_name}"), check_for_found_class=False)
    async def add_action(self, action_name:str, action:Action):
        return await self.post(f"/actions/{action_name}", action)
    async def set_action(self, action_name:str, action:Action):
        return await self.put(f"/actions/{action_name}", action)
    async def delete_action(self, action_name:str):
        return await self.delete(f"/actions/{action_name}")
    async def execute_action(self, action_name:str):
        return await self.get(f"/actions/{action_name}/execute")
    async def reschedule_action(self, action_name:str):
        return await self.get(f"/actions/{action_name}/reschedule")
    async def unschedule_action(self, action_name:str):
        return await self.get(f"/actions/{action_name}/unschedule")

    # /schedulers
    async def schedule_action(self, scheduler_name:str, action_name:str):
        return await self.get(f"/schedulers/{scheduler_name}/actions/{action_name}")
    async def get_scheduler(self, scheduler_name:str):
        return resolve_scheduler(await self.get_as_json(f"/schedulers/{scheduler_name}"), check_for_found_class=False)
    async def add_scheduler(self, scheduler_name:str, scheduler:Scheduler):
        return await self.post(f"/schedulers/{scheduler_name}", scheduler)
    async def set_scheduler(self, scheduler_name:str, scheduler:Scheduler):
        return await self.put(f"/schedulers/{scheduler_name}", scheduler)
    async def delete_scheduler(self, scheduler_name:str):
        return await self.delete(f"/schedulers/{scheduler_name}")
    async def unschedule_scheduler(self, scheduler_name:str):
        return await self.get(f"/schedulers/{scheduler_name}/unschedule")
    async def reschedule_all_schedulers(self):
        return await self.get(f"/schedulers/reschedule_all")
    async def execute_scheduler_actions(self, scheduler_name:str):
        return await self.get(f"/schedulers/{scheduler_name}/execute")

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
    async def get(self, path:str):
        async with AsyncClient(base_url=self.base_url()) as ac:
            return await ac.get(url=path)
    async def get_as_json(self, path:str):
        async with AsyncClient(base_url=self.base_url()) as ac:
            response = await ac.get(url=path)
            return response.json()
    async def put(self, path:str, data:BaseModel):
        async with AsyncClient(base_url=self.base_url()) as ac:
            return await ac.put(url=path, data=data.json())
    async def post(self, path:str, data:BaseModel):
        async with AsyncClient(base_url=self.base_url()) as ac:
            return await ac.post(url=path, data=data.json())
    async def delete(self, path:str):
        async with AsyncClient(base_url=self.base_url()) as ac:
            return await ac.delete(url=path)

    def base_url(self):
        return f"http://{self.host}:{self.port}"