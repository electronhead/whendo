import logging
from enum import Enum
from typing import Optional, Dict, Set, Any
from whendo.core.util import Now, Http, KeyTagMode, DateTime2, DateTime
from whendo.core.hooks import DispatcherHooks
from whendo.core.action import Action


logger = logging.getLogger(__name__)


class DispActionMode(str, Enum):
    """
    usage:
        DispActionMode.FIELD
    """

    FIELD = "field"
    DATA = "data"


class DispatcherAction(Action):
    """
    Instances of subclasses of DispatcherAction invoke Dispatcher
    methods directly by way of the class, DispatcherHooks.

    The class's fields determine the variable set necessary for
    successful execution of the action. With this in mind, the
    action draws these variable values from two sources: the instance's
    fields and the 'data' argument of the execute method.

    The mode field prioritizes which source to favor for the execution
    of the action. Modes are either FIELD or DATA.

    FIELD:

        the instance variables are the first choice for values used
        in the action's execute method. If an instance variable is
        absent (==None), then the execute method looks for the value
        in the incoming 'data' dictionary.

        'FIELD' is the default mode.

    DATA:

        the dictionary items in the incoming 'data' dictionary argument
        are the first choice for values used in the execute method. If
        a dictionary key is absent, then the execute method looks for the
        value in the instance variables of the action object.

    [Note the use of self.getResult()]
    """

    mode: DispActionMode = DispActionMode.FIELD

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
                if self.mode == DispActionMode.DATA:
                    args.update(data_args)
                else:
                    data_args.update(args)
                    args = data_args
        return args


class ScheduleProgram(DispatcherAction):
    program_name: Optional[str] = None
    start_stop: Optional[DateTime2] = None
    schedule_program: str = "schedule_program"

    def description(self):
        return f"This action schedules a program with mode ({self.mode}) and fields: program_name ({self.program_name}), start ({self.start}), stop ({self.stop})."

    def execute(self, tag: str = None, data: dict = None):
        args: Dict[str, Any] = {
            "program_name": self.program_name,
            "start_stop": self.start_stop,
        }
        args = self.compute_args(args, data)
        program_name = args["program_name"]
        if not program_name:
            raise ValueError(f"program name missing")
        start_stop = args["start_stop"]
        if not start_stop:
            raise ValueError(f"start_stop missing")
        DispatcherHooks.schedule_program(
            program_name=program_name, start=start_stop.dt1, stop=start_stop.dt2
        )
        result = f"program ({program_name}) scheduled, start_stop({start_stop})"
        return self.action_result(result=result, data=data, extra=args)


class UnscheduleProgram(DispatcherAction):
    program_name: Optional[str] = None
    unschedule_program: str = "unschedule_program"

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
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    schedule_action: str = "schedule_action"

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
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    unschedule_scheduler_action: str = "unschedule_scheduler_action"

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
    scheduler_name: Optional[str] = None
    unschedule_scheduler: str = "unschedule_scheduler"

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
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    wait_until: Optional[DateTime] = None
    defer_action: str = "defer_action"

    def description(self):
        return f"This action defers a schedule/action with mode ({self.mode}) and fields: scheduler_name ({self.scheduler_name}), action_name ({self.action_name}), wait_until ({self.wait_until})."

    def execute(self, tag: str = None, data: dict = None):
        # gather all of the args that can participate
        args: Dict[str, Any] = {
            "scheduler_name": self.scheduler_name,
            "action_name": self.action_name,
            "wait_until": self.wait_until,
        }
        args = self.compute_args(args, data)
        scheduler_name = args["scheduler_name"]
        if not scheduler_name:
            raise ValueError("scheduler name missing")
        action_name = args["action_name"]
        if not action_name:
            raise ValueError("action name missing")
        wait_until = args["wait_until"]
        if not wait_until:
            raise ValueError("wait_until missing")
        DispatcherHooks.defer_action(
            scheduler_name=scheduler_name,
            action_name=action_name,
            wait_until=wait_until.dt,
        )
        result = f"action ({action_name}) using scheduler ({scheduler_name}) deferred until ({wait_until})"

        return self.action_result(result=result, data=data, extra=args)


class ExpireAction(DispatcherAction):
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    expire_on: Optional[DateTime] = None
    expire_action: str = "expire_action"

    def description(self):
        return f"This action expires a schedule/action with mode ({self.mode}) and fields: scheduler_name ({self.scheduler_name}), action_name ({self.action_name}), expire_on ({self.expire_on})."

    def execute(self, tag: str = None, data: dict = None):
        # gather all of the args that can participate
        args: Dict[str, Any] = {
            "scheduler_name": self.scheduler_name,
            "action_name": self.action_name,
            "expire_on": self.expire_on,
        }
        args = self.compute_args(args, data)
        scheduler_name = args["scheduler_name"]
        if not scheduler_name:
            raise ValueError("scheduler name missing")
        action_name = args["action_name"]
        if not action_name:
            raise ValueError("action name missing")
        expire_on = args["expire_on"]
        if not expire_on:
            raise ValueError("expire_on missing")
        DispatcherHooks.expire_action(
            scheduler_name=scheduler_name,
            action_name=action_name,
            expire_on=expire_on.dt,
        )
        result = f"action ({action_name}) using scheduler ({scheduler_name}) expiring on ({expire_on})"
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


class Exec(DispatcherAction):
    """
    Execute an action at a server.
    """

    server_name: Optional[str] = None
    action_name: Optional[str] = None
    exec: str = "exec"

    def description(self):
        return f"This action executes ({self.action_name}) at the server ({self.server_name})."

    def execute(self, tag: str = None, data: dict = None):
        args = {"server_name": self.server_name, "action_name": self.action_name}
        args = self.compute_args(args, data)
        server_name = args["server_name"]
        action_name = args["action_name"]
        if not action_name:
            raise ValueError(f"action name missing")
        host = None
        port = None
        if server_name:
            server = DispatcherHooks.get_server(server_name)
            host = server.host
            port = server.port
        else:
            host = self.local_host()
            port = self.local_port()

        if data:
            if host == self.local_host() and port == self.local_port():
                # execute locally
                result = DispatcherHooks.get_action(action_name).execute(
                    tag=tag, data=data
                )
            else:
                result = Http(host=host, port=port).post_dict(
                    f"/actions/{action_name}/execute", data
                )
        else:
            if host == self.local_host() and port == self.local_port():
                # execute locally
                result = DispatcherHooks.get_action(action_name).execute(tag=tag)
            else:
                result = Http(host=server.host, port=server.port).get(
                    f"/actions/{action_name}/execute"
                )
        return self.action_result(result=result, data=data)


class ExecKeyTags(DispatcherAction):
    """
    Execute an action at zero or more servers. If key_tags is not provided, executes action at all servers.
    """

    action_name: Optional[str] = None
    key_tags: Optional[Dict[str, Set[str]]] = None
    key_tag_mode: KeyTagMode = KeyTagMode.ANY
    exec_key_tags: str = "exec_key_tags"

    def description(self):
        return f"This action executes ({self.action_name}) at the servers with key:tags satisfying ({self.key_tags}) using key tag mode ({self.key_tag_mode})."

    def execute(self, tag: str = None, data: dict = None):
        args: Dict[str, Any] = {
            "action_name": self.action_name,
            "key_tags": self.key_tags,
            "key_tag_mode": self.key_tag_mode,
        }
        args = self.compute_args(args, data)
        action_name = args["action_name"]
        if not action_name:
            raise ValueError(f"action name missing")
        key_tags = args["key_tags"]
        key_tag_mode = args["key_tag_mode"]

        if key_tags:
            servers = DispatcherHooks.get_servers_by_tags(
                key_tags=key_tags, key_tag_mode=key_tag_mode
            )
        else:
            servers = DispatcherHooks.get_servers()
        result = []
        if data:
            for server in servers:
                if (
                    server.host == self.local_host()
                    and server.port == self.local_port()
                ):
                    # execute locally
                    result.append(
                        DispatcherHooks.get_action(action_name).execute(
                            tag=tag, data=data
                        )
                    )
                else:
                    result.append(
                        Http(host=server.host, port=server.port).post_dict(
                            f"/actions/{action_name}/execute", data
                        )
                    )
        else:
            for server in servers:
                if (
                    server.host == self.local_host()
                    and server.port == self.local_port()
                ):
                    # execute locally
                    result.append(
                        DispatcherHooks.get_action(action_name).execute(tag=tag)
                    )
                else:
                    result.append(
                        Http(host=server.host, port=server.port).get(
                            f"/actions/{action_name}/execute"
                        )
                    )
        return self.action_result(result=result, data=data)


class ExecSupplied(DispatcherAction):
    """
    Execute an action at a server.
    """

    server_name: Optional[str] = None
    action: Optional[Action] = None
    exec_supplied: str = "exec_supplied"

    def description(self):
        return (
            f"This action executes ({self.action}) at the server ({self.server_name})."
        )

    def execute(self, tag: str = None, data: dict = None):
        args: Dict[str, Any] = {"server_name": self.server_name, "action": self.action}
        args = self.compute_args(args, data)
        server_name = args["server_name"]
        action = args["action"]
        if not action:
            raise ValueError(f"action missing")
        host = None
        port = None
        if server_name:
            server = DispatcherHooks.get_server(server_name)
            host = server.host
            port = server.port
        else:
            host = self.local_host()
            port = self.local_port()

        if data:
            if host == self.local_host() and port == self.local_port():
                # execute locally
                result = action.execute(tag=tag, data=data)
            else:
                composite = {"data": data, "supplied_action_as_dict": action.dict()}
                result = Http(host=host, port=port).post_dict(
                    f"/execution/with_data", composite
                )
        else:
            if host == self.local_host() and port == self.local_port():
                # execute locally
                result = action.execute(tag=tag)
            else:
                result = Http(host=server.host, port=server.port).post(
                    f"/execution", action
                )
        return self.action_result(result=result, data=data)


class ExecSuppliedKeyTags(DispatcherAction):
    """
    Execute an action at zero or more servers. If key_tags is not provided, executes action at all servers.
    """

    action: Optional[Action] = None
    key_tags: Optional[Dict[str, Set[str]]] = None
    key_tag_mode: KeyTagMode = KeyTagMode.ANY
    exec_supplied_key_tags: str = "exec_supplied_key_tags"

    def description(self):
        return f"This action executes ({self.action}) at the servers with key:tags satisfying ({self.key_tags}) using key tag mode ({self.key_tag_mode})."

    def execute(self, tag: str = None, data: dict = None):
        args: Dict[str, Any] = {
            "action": self.action,
            "key_tags": self.key_tags,
            "key_tag_mode": self.key_tag_mode,
        }
        args = self.compute_args(args, data)
        action = args["action"]
        if not action:
            raise ValueError(f"action missing")
        key_tags = args["key_tags"]
        key_tag_mode = args["key_tag_mode"]

        if key_tags:
            servers = DispatcherHooks.get_servers_by_tags(
                key_tags=key_tags, key_tag_mode=key_tag_mode
            )
        else:
            servers = DispatcherHooks.get_servers()
        result = []
        if data:
            for server in servers:
                if (
                    server.host == self.local_host()
                    and server.port == self.local_port()
                ):
                    # execute locally
                    result.append(action.execute(tag=tag, data=data))
                else:
                    composite = {"supplied_action_as_dict": action.dict(), "data": data}
                    result.append(
                        Http(host=server.host, port=server.port).post_dict(
                            f"/execution/with_data", composite
                        )
                    )
        else:
            for server in servers:
                if (
                    server.host == self.local_host()
                    and server.port == self.local_port()
                ):
                    # execute locally
                    result.append(action.execute(tag=tag))
                else:
                    result.append(
                        Http(host=server.host, port=server.port).post(
                            f"/execution", action
                        )
                    )
        return self.action_result(result=result, data=data)
