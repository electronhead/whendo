import logging
from typing import Optional, Dict, Set, Any
from whendo.core.util import Now, Http, KeyTagMode, DateTime2, DateTime
from whendo.core.hooks import DispatcherHooks
from whendo.core.action import Action, ActionRez, Rez, log_action_result
from whendo.core.resolver import resolve_rez, resolve_action


logger = logging.getLogger(__name__)


class DispatcherAction(Action):
    """
    Instances of subclasses of DispatcherAction invoke Dispatcher
    methods directly by way of the class, DispatcherHooks.
    """


class ScheduleProgram(DispatcherAction):
    program_name: Optional[str] = None
    start_stop: Optional[DateTime2] = None
    schedule_program: str = "schedule_program"

    def description(self):
        return f"This action schedules a program ({self.program_name}) start_stop ({self.start_stop})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        program_name = flds.get("program_name", None)
        if program_name == None:
            raise ValueError("program name missing")
        start_stop = flds.get("start_stop", None)
        if start_stop == None:
            raise ValueError(f"start_stop missing")
        DispatcherHooks.schedule_program(
            program_name=program_name, start=start_stop.dt1, stop=start_stop.dt2
        )
        result = f"program ({program_name}) scheduled, start_stop({start_stop})"
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class UnscheduleProgram(DispatcherAction):
    program_name: Optional[str] = None
    unschedule_program: str = "unschedule_program"

    def description(self):
        return f"This action unschedules a program ({self.program_name})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        program_name = flds.get("program_name", None)
        if program_name == None:
            raise ValueError("program name missing")
        DispatcherHooks.unschedule_program(program_name=program_name)
        result = f"program ({program_name}) unscheduled"
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class UnscheduleActiveProgram(DispatcherAction):
    program_name: Optional[str] = None
    unschedule_active_program: str = "unschedule_active_program"

    def description(self):
        return f"This action unschedules the active elements of program ({self.program_name})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        program_name = flds.get("program_name", None)
        if program_name == None:
            raise ValueError("program name missing")
        DispatcherHooks.unschedule_active_program(program_name=program_name)
        result = f"active program ({program_name}) elements unscheduled"
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class ScheduleAction(DispatcherAction):
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    schedule_action: str = "schedule_action"

    def description(self):
        return f"This action schedules an action ({self.action_name}) using scheduler ({self.scheduler_name})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        scheduler_name = flds.get("scheduler_name", None)
        if scheduler_name == None:
            raise ValueError("scheduler name missing")
        action_name = flds.get("action_name", None)
        if action_name == None:
            raise ValueError("action name missing")
        DispatcherHooks.schedule_action(
            scheduler_name=scheduler_name, action_name=action_name
        )
        result = f"action ({action_name}) scheduled using scheduler ({scheduler_name})"
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class UnscheduleSchedulerAction(DispatcherAction):
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    unschedule_scheduler_action: str = "unschedule_scheduler_action"

    def description(self):
        return f"This action unschedules an action ({self.action_name}) with scheduler ({self.scheduler_name})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        scheduler_name = flds.get("scheduler_name", None)
        if scheduler_name == None:
            raise ValueError("scheduler name missing")
        action_name = flds.get("action_name", None)
        if action_name == None:
            raise ValueError("action name missing")
        DispatcherHooks.unschedule_scheduler_action(
            scheduler_name=scheduler_name, action_name=action_name
        )
        result = f"action ({action_name}) unscheduled from scheduler ({scheduler_name})"
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class UnscheduleScheduler(DispatcherAction):
    scheduler_name: Optional[str] = None
    unschedule_scheduler: str = "unschedule_scheduler"

    def description(self):
        return f"This action unschedules a scheduler ({self.scheduler_name})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        scheduler_name = flds.get("scheduler_name", None)
        if scheduler_name == None:
            raise ValueError("scheduler name missing")
        DispatcherHooks.unschedule_scheduler(scheduler_name=scheduler_name)
        result = f"scheduler ({scheduler_name}) unscheduled"
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class UnscheduleAllSchedulers(DispatcherAction):
    unschedule_all_schedulers: str = "unschedule_all_schedulers"

    def description(self):
        return f"This action unschedules all schedulers."

    def execute(self, tag: str = None, rez: Rez = None):
        DispatcherHooks.unschedule_all_schedulers()
        result = f"all schedulers unscheduled"
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class DeferAction(DispatcherAction):
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    wait_until: Optional[DateTime] = None
    defer_action: str = "defer_action"

    def description(self):
        return f"This action defers a schedule/action with mode ({self.mode}) and fields: scheduler_name ({self.scheduler_name}), action_name ({self.action_name}), wait_until ({self.wait_until})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        scheduler_name = flds.get("scheduler_name", None)
        if scheduler_name == None:
            raise ValueError("scheduler name missing")
        action_name = flds.get("action_name", None)
        if not action_name:
            raise ValueError("action name missing")
        wait_until = flds.get("wait_until", None)
        if not wait_until:
            raise ValueError("wait_until missing")
        DispatcherHooks.defer_action(
            scheduler_name=scheduler_name,
            action_name=action_name,
            wait_until=wait_until.dt,
        )
        result = f"action ({action_name}) using scheduler ({scheduler_name}) deferred until ({wait_until})"

        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class ExpireAction(DispatcherAction):
    scheduler_name: Optional[str] = None
    action_name: Optional[str] = None
    expire_on: Optional[DateTime] = None
    expire_action: str = "expire_action"

    def description(self):
        return f"This action expires a schedule/action with mode ({self.mode}) and fields: scheduler_name ({self.scheduler_name}), action_name ({self.action_name}), expire_on ({self.expire_on})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        scheduler_name = flds.get("scheduler_name", None)
        if scheduler_name == None:
            raise ValueError("scheduler name missing")
        action_name = flds.get("action_name", None)
        if action_name == None:
            raise ValueError("action name missing")
        expire_on = flds.get("expire_on", None)
        if expire_on == None:
            raise ValueError("expire_on missing")
        DispatcherHooks.expire_action(
            scheduler_name=scheduler_name,
            action_name=action_name,
            expire_on=expire_on.dt,
        )
        result = f"action ({action_name}) using scheduler ({scheduler_name}) expiring on ({expire_on})"
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class ClearAllDeferredActions(DispatcherAction):
    clear_all_deferred_actions: str = "clear_all_deferred_actions"

    def description(self):
        return "Removes all deferred scheduled actions."

    def execute(self, tag: str = None, rez: Rez = None):
        DispatcherHooks.clear_all_deferred_actions()
        result = "All deferred scheduled actions removed."
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class ClearAllExpiringActions(DispatcherAction):
    clear_all_expiring_actions: str = "clear_all_expiring_actions"

    def description(self):
        return "Removes all expiring scheduled actions."

    def execute(self, tag: str = None, rez: Rez = None):
        DispatcherHooks.clear_all_expiring_actions()
        result = "All expiring scheduled actions removed."
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class ClearAllScheduling(DispatcherAction):
    clear_all_scheduling: str = "clear_all_scheduling"

    def description(self):
        return "Removes all scheduled actions, current or planned, and foreground Timed instance jobs. Ignores the 'inventory' objects and the out-of-band Timed instance."

    def execute(self, tag: str = None, rez: Rez = None):
        DispatcherHooks.clear_all_scheduling()
        result = "All scheduling artifacts cleared or reset."
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class Exec(DispatcherAction):
    """
    Execute an action at a server.
    """

    server_name: Optional[str] = None
    action_name: Optional[str] = None
    exec: str = "exec"

    def description(self):
        return f"This action executes ({self.action_name}) at the server ({self.server_name})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        server_name = flds.get("server_name", None)
        action_name = flds.get("action_name", None)
        if action_name == None:
            raise ValueError(f"action name missing")
        if server_name == None:
            host = self.local_host()
            port = self.local_port()
            is_local = True
        else:
            server = DispatcherHooks.get_server(server_name)
            host = server.host
            port = server.port
            is_local = False

        if rez:
            if is_local:
                # execute locally
                action = DispatcherHooks.get_action(action_name)
                result = action.execute(tag=tag, rez=rez)
                log_action_result(
                    calling_logger=logger,
                    calling_object=self,
                    tag=tag,
                    action=action,
                    result=result,
                )
            else:
                response = Http(host=host, port=port).post(
                    f"/actions/{action_name}/execute", rez
                )
                result = resolve_rez(response)
        else:
            if is_local:
                # execute locally
                action = DispatcherHooks.get_action(action_name)
                result = action.execute(tag=tag)
                log_action_result(
                    calling_logger=logger,
                    calling_object=self,
                    tag=tag,
                    action=action,
                    result=result,
                )
            else:
                response = Http(host=server.host, port=server.port).get(
                    f"/actions/{action_name}/execute"
                )
                result = resolve_rez(response)

        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class ExecKeyTags(DispatcherAction):
    """
    Execute an action at zero or more servers. If key_tags is not provided, executes action at all servers.
    """

    action_name: Optional[str] = None
    key_tags: Optional[Dict[str, Set[str]]] = None
    key_tag_mode: Optional[KeyTagMode] = None
    exec_key_tags: str = "exec_key_tags"

    def description(self):
        return f"This action executes ({self.action_name}) at the servers with key:tags satisfying ({self.key_tags}) using key tag mode ({self.key_tag_mode})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        action_name = flds.get("action_name", None)
        if action_name == None:
            raise ValueError(f"action name missing")
        key_tags = flds.get("key_tags", None)
        key_tag_mode = flds.get("key_tag_mode", KeyTagMode.ANY)

        if key_tags:
            servers = DispatcherHooks.get_servers_by_tags(
                key_tags=key_tags, key_tag_mode=key_tag_mode
            )
        else:
            servers = DispatcherHooks.get_servers()
        result = []
        if rez:
            for server in servers:
                if (
                    server.host == self.local_host()
                    and server.port == self.local_port()
                ):
                    # execute locally
                    action = DispatcherHooks.get_action(action_name)
                    action_rez = action.execute(tag=tag, rez=rez)
                    result.append(action_rez)
                    log_action_result(
                        calling_logger=logger,
                        calling_object=self,
                        tag=tag,
                        action=action,
                        result=action_rez,
                    )
                else:
                    response = Http(host=server.host, port=server.port).post(
                        f"/actions/{action_name}/execute", rez
                    )
                    result.append(resolve_rez(response))
        else:
            for server in servers:
                if (
                    server.host == self.local_host()
                    and server.port == self.local_port()
                ):
                    # execute locally
                    action = DispatcherHooks.get_action(action_name)
                    action_rez = action.execute(tag=tag)
                    result.append(action_rez)
                    log_action_result(
                        calling_logger=logger,
                        calling_object=self,
                        tag=tag,
                        action=action,
                        result=action_rez,
                    )
                else:
                    response = Http(host=server.host, port=server.port).get(
                        f"/actions/{action_name}/execute"
                    )
                    result.append(resolve_rez(response))
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


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

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        action = flds.get("action", None)
        if action == None:
            raise ValueError(f"action missing")
        if isinstance(action, dict):
            action = resolve_action(action)
        server_name = flds.get("server_name", None)
        if server_name == None:
            host = self.local_host()
            port = self.local_port()
            is_local = True
        else:
            server = DispatcherHooks.get_server(server_name)
            host = server.host
            port = server.port
            is_local = False
        if rez:
            if is_local:
                # execute locally
                result = action.execute(tag=tag)
                log_action_result(
                    calling_logger=logger,
                    calling_object=self,
                    tag=tag,
                    action=action,
                    result=result,
                )
            else:
                action_rez = ActionRez(action=action, rez=rez)
                response = Http(host=host, port=port).post(
                    f"/execution/with_rez", action_rez
                )
                result = resolve_rez(response)
        else:
            if is_local:
                # execute locally
                result = action.execute(tag=tag)
                log_action_result(
                    calling_logger=logger,
                    calling_object=self,
                    tag=tag,
                    action=action,
                    result=result,
                )
            else:
                response = Http(host=server.host, port=server.port).post(
                    f"/execution", action
                )
                result = resolve_rez(response)
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class ExecSuppliedKeyTags(DispatcherAction):
    """
    Execute an action at zero or more servers. If key_tags is not provided, executes action at all servers.
    """

    action: Optional[Action] = None
    key_tags: Optional[Dict[str, Set[str]]] = None
    key_tag_mode: Optional[KeyTagMode] = None
    exec_supplied_key_tags: str = "exec_supplied_key_tags"

    def description(self):
        return f"This action executes ({self.action}) at the servers with key:tags satisfying ({self.key_tags}) using key tag mode ({self.key_tag_mode})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        action = flds.get("action", None)
        if action == None:
            raise ValueError(f"action missing")
        if isinstance(action, dict):
            action = resolve_action(action)
        key_tags = flds.get("key_tags", None)
        key_tag_mode = flds.get("key_tag_mode", KeyTagMode.ANY)
        if key_tags:
            servers = DispatcherHooks.get_servers_by_tags(
                key_tags=key_tags, key_tag_mode=key_tag_mode
            )
        else:
            servers = DispatcherHooks.get_servers()
        result = []
        if rez:
            for server in servers:
                if (
                    server.host == self.local_host()
                    and server.port == self.local_port()
                ):
                    # execute locally
                    action_rez = action.execute(tag=tag, rez=rez)
                    result.append(action_rez)
                    log_action_result(
                        calling_logger=logger,
                        calling_object=self,
                        tag=tag,
                        action=action,
                        result=action_rez,
                    )
                else:
                    action_rez = ActionRez(action=action, rez=rez)
                    response = Http(host=server.host, port=server.port).post(
                        f"/execution/with_rez", action_rez
                    )
                    result.append(resolve_rez(response))
        else:
            for server in servers:
                if (
                    server.host == self.local_host()
                    and server.port == self.local_port()
                ):
                    # execute locally
                    action_rez = action.execute(tag=tag)
                    result.append(action_rez)
                    log_action_result(
                        calling_logger=logger,
                        calling_object=self,
                        tag=tag,
                        action=action,
                        result=action_rez,
                    )
                else:
                    response = Http(host=server.host, port=server.port).post(
                        f"/execution", action
                    )
                    result.append(resolve_rez(response))
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})


class SchedulingInfo(Action):
    """
    Returns scheduling related info found in Dispatcher fields:
        scheduled_actions: ScheduledActions
        deferred_scheduled_actions: DatedScheduledActions
        expiring_scheduled_actions: DatedScheduledActions
        deferred_programs: DeferredPrograms
    """

    scheduling_info: str = "scheduling_info"

    def description(self):
        return f"This action returns active scheduling information"

    def execute(self, tag: str = None, rez: Rez = None):
        return self.action_result(
            result=DispatcherHooks.get_scheduling_info(),
            rez=rez,
            flds=rez.flds if rez else {},
        )


class DispatcherDump(Action):
    """
    Returns Dispatcher.load_current()
    """

    dispatcher_dump: str = "dispatcher_dump"

    def description(self):
        return f"This action returns the contents of the active Dispatcher"

    def execute(self, tag: str = None, rez: Rez = None):
        return self.action_result(
            result=DispatcherHooks.get_dispatcher_dump(),
            rez=rez,
            flds=rez.flds if rez else {},
        )
