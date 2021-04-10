import logging
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from whendo.core.util import DispatcherHooks, Now
from whendo.core.action import Action


logger = logging.getLogger(__name__)


class DispActionMode(str, Enum):
    """
    usage:
        DispActionMode.field
    """

    field = "field"
    data = "data"


class DispatcherAction(Action):
    """
    Instances of subclasses of DispatcherAction invoke Dispatcher
    methods directly by way of the class, DispatcherHooks.

    The class's fields determine the variable set necessary for
    successful execution of the action. With this in mind, the
    action draws these variable values from two sources: the instance's
    fields and the 'data' argument of the execute method.

    The mode field prioritizes which source to favor for the execution
    of the action. Modes are either "field" or "data".

    field:

        the instance variables are the first choice for values used
        in the action's execute method. If an instance variable is
        absent (==None), then the execute method looks for the value
        in the incoming 'data' dictionary.

        'field' is the default mode.

    data:

        the dictionary items in the incoming 'data' dictionary argument
        are the first choice for values used in the execute method. If
        a dictionary key is absent, then the execute method looks for the
        value in the instance variables of the action object.

    [Note the use of self.getResult()]
    """

    dispatcher_action: str = "dispatcher_action"
    mode: DispActionMode = DispActionMode.field

    def compute_args(self, args: dict, data: dict = None):
        """
        Implements field vs. data mode logic.
        """
        if data:
            data_result = self.get_result(data)
            data_args = {
                arg: data_result[arg] for arg in args.keys() if arg in data_result
            }
            if self.mode == DispActionMode.data:
                args.update(data_args)
            else:
                data_args.update(args)
                args = data_args
        return args


class ScheduleProgram(DispatcherAction):
    program_name: Optional[str] = None
    start: Optional[datetime] = None
    stop: Optional[datetime] = None

    def description(self):
        pass

    def execute(self, tag: str = None, data: dict = None):
        args = {
            "program_name": self.program_name,
            "start": self.start,
            "stop": self.stop,
        }
        args = self.compute_args(args, data)
        DispatcherHooks.schedule_program(**args)
        result = f"program ({args['program_name']}) scheduled, start({args['start']}) stop({args['stop']})"
        return self.action_result(result=result, data=data, extra=args)


class UnscheduleProgram(DispatcherAction):
    program_name: Optional[str] = None

    def description(self):
        pass

    def execute(self, tag: str = None, data: dict = None):
        args = {
            "program_name": self.program_name,
        }
        args = self.compute_args(args, data)
        DispatcherHooks.unschedule_program(**args)
        result = f"program ({args['program_name']}) unscheduled"
        return self.action_result(result=result, data=data, extra=args)


class ScheduleAction(DispatcherAction):
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None

    def description(self):
        return f""

    def execute(self, tag: str = None, data: dict = None):
        # gather all of the args that can participate
        args = {"scheduler_name": self.scheduler_name, "action_name": self.action_name}
        args = self.compute_args(args, data)
        DispatcherHooks.schedule_action(**args)
        result = f"action ({args['action_name']}) scheduled using scheduler ({args['scheduler_name']})"
        return self.action_result(result=result, data=data, extra=args)


class DeferAction(DispatcherAction):
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
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
        args = self.compute_args(args, data)
        DispatcherHooks.defer_action(**args)
        result = f"action ({args['action_name']}) using scheduler ({args['scheduler_name']}) deferred until ({args['wait_until']})"

        return self.action_result(result=result, data=data, extra=args)


class ExpireAction(DispatcherAction):
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    expire_on: Optional[datetime] = None

    def description(self):
        return f""

    def execute(self, tag: str = None, data: dict = None):
        # gather all of the args that can participate
        args = {
            "scheduler_name": self.scheduler_name,
            "action_name": self.action_name,
            "expire_on": self.expire_on,
        }
        args = self.compute_args(args, data)
        DispatcherHooks.expire_action(**args)
        result = f"action ({args['action_name']}) using scheduler ({args['scheduler_name']}) expiring on ({args['expire_on']})"
        return self.action_result(result=result, data=data, extra=args)
