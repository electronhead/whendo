import logging
from typing import Optional
from datetime import datetime, timedelta
from whendo.core.util import DispatcherHooks, Now
from whendo.core.action import Action


logger = logging.getLogger(__name__)


class ScheduleProgram(Action):
    program_name: str
    start: datetime
    stop: datetime

    def description(self):
        pass

    def execute(self, tag: str = None, data: dict = None):
        args = {
            "program_name": self.program_name,
            "start": self.start,
            "stop": self.stop,
        }
        if data:
            data_result = self.get_result(data)
            data_args = {
                arg: data_result[arg] for arg in args.keys() if arg in data_result
            }
            args.update(data_args)
        DispatcherHooks.schedule_program(**args)
        result = f"program ({args['program_name']}) scheduled, start({args['start']}) stop({args['stop']})"
        return self.action_result(result=result, data=data)


class UnscheduleProgram(Action):
    program_name: str

    def description(self):
        pass

    def execute(self, tag: str = None, data: dict = None):
        args = {
            "program_name": self.program_name,
        }
        if data:
            data_result = self.get_result(data)
            data_args = {
                arg: data_result[arg] for arg in args.keys() if arg in data_result
            }
            args.update(data_args)
        DispatcherHooks.unschedule_program(**args)
        result = f"program ({args['program_name']}) unscheduled"
        return self.action_result(result=result, data=data)


class ScheduleAction(Action):
    scheduler_name: str
    action_name: str

    def description(self):
        return f""

    def execute(self, tag: str = None, data: dict = None):
        # gather all of the args that can participate
        args = {"scheduler_name": self.scheduler_name, "action_name": self.action_name}
        if data:
            data_result = self.get_result(data)
            data_args = {
                arg: data_result[arg] for arg in args.keys() if arg in data_result
            }
            args.update(self.get_result(data_args))
        DispatcherHooks.schedule_action(**args)
        result = f"action ({args['action_name']})scheduled using scheduler ({args['scheduler_name']})"
        return self.action_result(result=result, data=data, extra=args)


class DeferAction(Action):
    scheduler_name: str
    action_name: str
    wait_until: Optional[datetime] = None

    def description(self):
        return f""

    def execute(self, tag: str = None, data: dict = None):
        # gather all of the args that can participate
        args = {
            "scheduler_name": self.scheduler_name,
            "action_name": self.action_name,
            "wait_until": self.wait_until,
        }
        if data:
            data_result = self.get_result(data)
            data_args = {
                arg: data_result[arg] for arg in args.keys() if arg in data_result
            }
            args.update(self.get_result(data_args))
        DispatcherHooks.defer_action(**args)
        result = f"action ({args['action_name']}) using scheduler ({args['scheduler_name']}) deferred until ({args['wait_until']})"

        return self.action_result(result=result, data=data, extra=args)


class ExpireAction(Action):
    scheduler_name: str
    action_name: str
    expire_on: datetime

    def description(self):
        return f""

    def execute(self, tag: str = None, data: dict = None):
        # gather all of the args that can participate
        args = {
            "scheduler_name": self.scheduler_name,
            "action_name": self.action_name,
            "expire_on": self.expire_on,
        }
        if data:
            data_result = self.get_result(data)
            data_args = {
                arg: data_result[arg] for arg in args.keys() if arg in data_result
            }
            args.update(self.get_result(data_args))
        DispatcherHooks.expire_action(**args)
        result = f"action ({args['action_name']}) using scheduler ({args['scheduler_name']}) expiring on ({args['expire_on']})"
        return self.action_result(result=result, data=data, extra=args)
