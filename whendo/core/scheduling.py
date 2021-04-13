from pydantic import BaseModel
from typing import Dict, List, Set, Callable
from datetime import datetime
from collections import namedtuple
import logging
from .util import Now, str_to_dt, dt_to_str


logger = logging.getLogger(__name__)


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


# dispatcher helper functions


def check_for_dated_actions(
    dated_scheduled_actions: Dict[str, ScheduledActions],
    schedule_update_thunk: Callable,
    verb: str,
):
    now = Now.dt()
    to_remove = []
    for date_time_str in dated_scheduled_actions:
        date_time = str_to_dt(date_time_str)
        if date_time < now:
            scheduled_actions = dated_scheduled_actions[date_time_str]
            for scheduler_name in scheduled_actions.scheduler_names():
                for action_name in scheduled_actions.actions(scheduler_name):
                    try:
                        schedule_update_thunk(scheduler_name, action_name)
                    except Exception as exception:
                        logger.error(
                            f"failed to {verb} action ({action_name}) under ({scheduler_name}) as of ({date_time_str})",
                            exception,
                        )
            to_remove.append(date_time_str)
    for date_time_str in to_remove:  # modify outside the previous for-loop
        dated_scheduled_actions.pop(date_time_str)


def apply_action_date(
    scheduler_name: str,
    action_name: str,
    date_time: datetime,
    dated_scheduled_actions: Dict[str, ScheduledActions],
):
    date_time_str = dt_to_str(date_time)
    if date_time_str not in dated_scheduled_actions:
        dated_scheduled_actions[date_time_str] = ScheduledActions()
    scheduled_actions = dated_scheduled_actions[date_time_str]
    scheduled_actions.add(scheduler_name, action_name)


def action_count(dated_scheduled_actions: Dict[str, ScheduledActions]):
    return sum(sa.action_count() for sa in dated_scheduled_actions.values())


def delete_dated_action(
    action_name: str, dated_scheduled_actions: Dict[str, ScheduledActions]
):
    date_time_str_to_remove = []
    for date_time_str in dated_scheduled_actions:
        scheduled_actions = dated_scheduled_actions[date_time_str]
        scheduled_actions.delete_action(action_name)
        if len(scheduled_actions.scheduler_names()) == 0:
            date_time_str_to_remove.append(date_time_str)
    for date_time_str in date_time_str_to_remove:
        dated_scheduled_actions.pop(date_time_str)


def delete_dated_scheduler(
    scheduler_name: str, dated_scheduled_actions: Dict[str, ScheduledActions]
):
    date_time_str_to_remove = []
    for date_time_str in dated_scheduled_actions:
        scheduled_actions = dated_scheduled_actions[date_time_str]
        scheduled_actions.delete_scheduler(scheduler_name)
        if len(scheduled_actions.scheduler_names()) == 0:
            date_time_str_to_remove.append(date_time_str)
    for date_time_str in date_time_str_to_remove:
        dated_scheduled_actions.pop(date_time_str)
