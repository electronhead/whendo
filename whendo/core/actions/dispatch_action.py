import logging
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from whendo.core.util import Now
from whendo.core.hooks import DispatcherHooks
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
        Implements field vs. data mode arg construction logic.
        """
        if data:
            data_result = self.get_result(data)
            if isinstance(data_result, dict):
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
    schedule_program: str = "schedule_program"
    program_name: Optional[str] = None
    start: Optional[datetime] = None
    stop: Optional[datetime] = None

    def description(self):
        return f"This action unschedules a program with mode ({self.mode}) and fields: program_name ({self.program_name}), start ({self.start}), stop ({self.stop})."

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
    unschedule_program: str = "unschedule_program"
    program_name: Optional[str] = None

    def description(self):
        return f"This action unschedules a program with mode ({self.mode}) and field: program_name ({self.program_name})."

    def execute(self, tag: str = None, data: dict = None):
        args = {
            "program_name": self.program_name,
        }
        args = self.compute_args(args, data)
        DispatcherHooks.unschedule_program(**args)
        result = f"program ({args['program_name']}) unscheduled"
        return self.action_result(result=result, data=data, extra=args)


class ScheduleAction(DispatcherAction):
    schedule_action: str = "schedule_action"
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None

    def description(self):
        return f"This action schedules an action with mode ({self.mode}) and fields: scheduler_name ({self.scheduler_name}), action_name ({self.action_name})."

    def execute(self, tag: str = None, data: dict = None):
        # gather all of the args that can participate
        args = {"scheduler_name": self.scheduler_name, "action_name": self.action_name}
        args = self.compute_args(args, data)
        DispatcherHooks.schedule_action(**args)
        result = f"action ({args['action_name']}) scheduled using scheduler ({args['scheduler_name']})"
        return self.action_result(result=result, data=data, extra=args)


class UnscheduleSchedulerAction(DispatcherAction):
    unschedule_scheduler_action: str = "unschedule_scheduler_action"
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None

    def description(self):
        return f"This action unschedules a scheduler/action with mode ({self.mode}) and fields: scheduler_name ({self.scheduler_name}), action_name ({self.action_name})."

    def execute(self, tag: str = None, data: dict = None):
        # gather all of the args that can participate
        args = {"scheduler_name": self.scheduler_name, "action_name": self.action_name}
        args = self.compute_args(args, data)
        DispatcherHooks.unschedule_scheduler_action(**args)
        result = f"action ({args['action_name']}) unscheduled from scheduler ({args['scheduler_name']})"
        return self.action_result(result=result, data=data, extra=args)


class UnscheduleScheduler(DispatcherAction):
    unschedule_scheduler: str = "unschedule_scheduler"
    scheduler_name: Optional[str] = None

    def description(self):
        return f"This action unschedules a scheduler with mode ({self.mode}) and field: scheduler_name ({self.scheduler_name})."

    def execute(self, tag: str = None, data: dict = None):
        # gather all of the args that can participate
        args = {"scheduler_name": self.scheduler_name}
        args = self.compute_args(args, data)
        DispatcherHooks.unschedule_scheduler(**args)
        result = f"scheduler ({args['scheduler_name']}) unscheduled"
        return self.action_result(result=result, data=data, extra=args)


class DeferAction(DispatcherAction):
    defer_action: str = "defer_action"
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    wait_until: Optional[datetime] = None

    def description(self):
        return f"This action defers a schedule/action with mode ({self.mode}) and fields: scheduler_name ({self.scheduler_name}), action_name ({self.action_name}), wait_until ({self.wait_until})."

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
    expire_action: str = "expire_action"
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    expire_on: Optional[datetime] = None

    def description(self):
        return f"This action expires a schedule/action with mode ({self.mode}) and fields: scheduler_name ({self.scheduler_name}), action_name ({self.action_name}), expire_on ({self.expire_on})."

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


class ClearAllDeferredActions(DispatcherAction):
    clear_all_deferred_actions: str = "clear_all_deferred_actions"

    def description(self):
        return "Removes all deferred scheduled actions."

    def execute(self, tag: str = None, data: dict = None):
        DispatcherHooks.clear_all_deferred_actions()
        result = "All deferred scheduled actions removed."
        return self.action_result(result=result, data=data)


class ClearAllExpiringActions(DispatcherAction):
    clear_all_expiring_actions: str = "clear_all_expiring_actions"

    def description(self):
        return "Removes all expiring scheduled actions."

    def execute(self, tag: str = None, data: dict = None):
        DispatcherHooks.clear_all_expiring_actions()
        result = "All expiring scheduled actions removed."
        return self.action_result(result=result, data=data)
