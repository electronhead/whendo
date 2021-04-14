from datetime import datetime
from typing import Callable


class DispatcherHooks:
    schedule_program_thunk: Callable
    unschedule_program_thunk: Callable
    schedule_action_thunk: Callable
    unschedule_scheduler_action_thunk: Callable
    unschedule_scheduler_thunk: Callable
    defer_action_thunk: Callable
    expire_action_thunk: Callable
    clear_all_deferred_actions_thunk: Callable
    clear_all_expiring_actions_thunk: Callable

    @classmethod
    def init(
        cls,
        schedule_program_thunk: Callable,
        unschedule_program_thunk: Callable,
        schedule_action_thunk: Callable,
        unschedule_scheduler_action_thunk: Callable,
        unschedule_scheduler_thunk: Callable,
        defer_action_thunk: Callable,
        expire_action_thunk: Callable,
        clear_all_deferred_actions_thunk: Callable,
        clear_all_expiring_actions_thunk: Callable,
    ):
        cls.schedule_program_thunk = schedule_program_thunk
        cls.unschedule_program_thunk = unschedule_program_thunk
        cls.schedule_action_thunk = schedule_action_thunk
        cls.unschedule_scheduler_action_thunk = unschedule_scheduler_action_thunk
        cls.unschedule_scheduler_thunk = unschedule_scheduler_thunk
        cls.defer_action_thunk = defer_action_thunk
        cls.expire_action_thunk = expire_action_thunk
        cls.clear_all_deferred_actions_thunk = clear_all_deferred_actions_thunk
        cls.clear_all_expiring_actions_thunk = clear_all_expiring_actions_thunk

    @classmethod
    def schedule_program(cls, program_name: str, start: datetime, stop: datetime):
        return cls.schedule_program_thunk(
            program_name=program_name, start=start, stop=stop
        )

    @classmethod
    def unschedule_program(cls, program_name: str):
        return cls.unschedule_program_thunk(program_name=program_name)

    @classmethod
    def schedule_action(cls, scheduler_name: str, action_name: str):
        return cls.schedule_action_thunk(
            scheduler_name=scheduler_name, action_name=action_name
        )

    @classmethod
    def unschedule_scheduler_action(cls, scheduler_name: str, action_name: str):
        return cls.unschedule_scheduler_action_thunk(
            scheduler_name=scheduler_name, action_name=action_name
        )

    @classmethod
    def unschedule_scheduler(cls, scheduler_name: str):
        return cls.unschedule_scheduler_thunk(scheduler_name=scheduler_name)

    @classmethod
    def defer_action(cls, scheduler_name: str, action_name: str, wait_until: datetime):
        return cls.defer_action_thunk(
            scheduler_name=scheduler_name,
            action_name=action_name,
            wait_until=wait_until,
        )

    @classmethod
    def expire_action(cls, scheduler_name: str, action_name: str, expire_on: datetime):
        return cls.expire_action_thunk(
            scheduler_name=scheduler_name, action_name=action_name, expire_on=expire_on
        )

    @classmethod
    def clear_all_deferred_actions(cls):
        return cls.clear_all_deferred_actions_thunk()

    @classmethod
    def clear_all_expiring_actions(cls):
        return cls.clear_all_expiring_actions_thunk()
