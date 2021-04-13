from pydantic import BaseModel
from typing import Dict, List, Set
from datetime import datetime
from collections import namedtuple
from .util import Now, dt_to_str, str_to_dt, add_to_list


class SchedulerActions(BaseModel):
    scheduler_name: str
    action_names: Set[str] = set()


class ScheduledActions(BaseModel):
    scheduler_actions: List[SchedulerActions] = []

    def add(self, scheduler_name: str, action_name: str):
        for sa in self.scheduler_actions:
            if sa.scheduler_name == scheduler_name:
                sa.action_names.add(action_name)
                return
        new_scheduler_action = SchedulerActions(
            scheduler_name=scheduler_name, action_names={action_name}
        )
        self.scheduler_actions.append(new_scheduler_action)

    def actions(self, scheduler_name: str):
        for sa in self.scheduler_actions:
            if sa.scheduler_name == scheduler_name:
                return sa.action_names
        return set()

    def delete(self, scheduler_name: str, action_name: str):
        to_remove = None
        for sa in self.scheduler_actions:
            if sa.scheduler_name == scheduler_name:
                if action_name in sa.action_names:
                    sa.action_names.remove(action_name)
                    if len(sa.action_names) == 0:
                        to_remove = sa
                break
        if to_remove:
            self.scheduler_actions.remove(to_remove)
            return to_remove.scheduler_name
        else:
            return None

    def delete_action(self, action_name: str):
        removed_scheduler_names: Set[str] = set()
        for scheduler_name in self.scheduler_names():
            to_remove = self.delete(scheduler_name, action_name)
            if to_remove:
                removed_scheduler_names.add(to_remove)
        return removed_scheduler_names

    def delete_scheduler(self, scheduler_name: str):
        for sa in self.scheduler_actions:
            if sa.scheduler_name == scheduler_name:
                self.scheduler_actions.remove(sa)
                return scheduler_name
        return None

    def scheduler_names(self):
        return set(sa.scheduler_name for sa in self.scheduler_actions)

    def action_names(self):
        action_names = set()
        for sa in self.scheduler_actions:
            action_names.update(sa.action_names)
        return action_names

    def action_count(self):
        return len(self.action_names())

    def clear(self):
        self.scheduler_actions.clear()


# DatetimeSchedulerActions = namedtuple(
#     "DatetimeSchedulerActions", ["datetime_str", "scheduler_actions"]
# )
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
