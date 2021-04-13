from pydantic import BaseModel
from typing import Dict, List, Set
from datetime import datetime
from collections import namedtuple
from .util import Now, dt_to_str, str_to_dt

ScheduledActions = namedtuple("ScheduledActions", ["scheduler_name", "action_names"])
class SchedulerActions(BaseModel):
    scheduled_actions:Set[ScheduledActions] = set()

    def add(self, scheduler_name:str, action_name:str):
        for sa in self.scheduled_actions:
            if sa.scheduler_name == scheduler_name:
                sa.action_names.add(action_name)
                return
        self.scheduled_actions.add(ScheduledActions(scheduler_name, {action_name}))
    
    def actions(self, scheduler_name:str):
        scheduler_actions = list(sa for sa in self.scheduled_actions if sa.scheduler_name == scheduler_name)
        if len(scheduler_actions) > 0:
            return scheduler_actions[0].action_names
        else:
            return set()
        
    
    def remove(self, scheduler_name:str, action_name:str):
        to_remove = None
        for sa in self.scheduled_actions:
            if sa.scheduler_name == scheduler_name:
                if action_name in sa.action_names:
                    sa.action_names.remove(action_name)
                    if len(sa.action_names) == 0:
                        to_remove = sa
                break
        if to_remove:
            self.scheduled_actions.remove(to_remove)
    
    def remove_scheduler(self, scheduler_name:str):
        self.scheduled_actions = set(sa for sa in self.scheduled_actions if sa.scheduler_name != scheduler_name)
    
    def scheduler_names(self):
        return set(sa.scheduler_name for sa in self.scheduled_actions)
    
    def clear(self):
        self.scheduler_actions.clear()
    
DatetimeSchedulerActions = namedtuple("DatetimeSchedulerActions", ["datetime_str", "scheduler_actions"])
# class ActionSchedule(BaseModel):
#     scheduled: SchedulerActions = SchedulerActions()
#     deferred: Dict[str, SchedulerActions] = {} # key is datetime string
#     expiring: Dict[str, SchedulerActions] = {} # key is datetime string

#     def add_scheduled(self, scheduler_name: str, action_name:str):
#         if scheduler_name not in self.scheduled:
#             self.scheduled[scheduler_name] = set()
#         self.scheduled[scheduler_name].add(action_name)
    
#     def delete_scheduled_scheduler(self, scheduler_name:str):
#         try:
#             self.scheduled.pop(scheduler_name)
#         except KeyError:
#             pass
    
#     def delete_scheduled_scheduler_action(self, scheduler_name:str, action_name:str):
#         try:
#             self.scheduled[scheduler_name].remove(action_name)
#         except KeyError:
#             pass


# default_action_schedule_name: str = "dispatcher"


# class ActionSchedules(BaseModel):
#     schedules: Dict[str, ActionSchedule] = {}  # key = ActionSchedule.name

#     def add_action_schedule(
#         self, action_schedule: ActionSchedule, name: str = default_action_schedule_name
#     ):
#         self.schedules[name] = action_schedule

#     def get_action_schedule(self, name: str = default_action_schedule_name):
#         return self.schedules.get(name, None)

#     def remove_action_schedule(self, name: str = default_action_schedule_name):
#         if name in self.schedules:
#             self.schedules.pop(name)


DeferredProgram = namedtuple("DeferredProgram", ["program_name", "start", "stop"])


class DeferredPrograms(BaseModel):
    deferred_programs: Set[DeferredProgram] = set()

    def add(self, deferred_program: DeferredProgram):
        self.deferred_programs.add(deferred_program)

    def pop(self):
        filtered = set(dp for dp in self.deferred_programs if dp.start < Now.dt())
        self.deferred_programs = self.deferred_programs - filtered
        return filtered

    def clear_program(self, program_name: str):
        self.deferred_programs = set(
            dp for dp in self.deferred_programs if dp.program_name != program_name
        )

    def clear(self):
        self.deferred_programs = set()

    def count(self):
        return len(self.deferred_programs)
