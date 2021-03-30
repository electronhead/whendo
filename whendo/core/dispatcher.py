"""
This class implements a single process-based system for defining and scheduling actions local
to the python runtime (api server, testing harness). The class implements all of the potential
endpoints of a restful api and supports testing outside of the restful api implementation.

Instances of this class contain Schedulers and Actions, which can at any point be submitted to and removed from the
job scheduling mechanism of the schedule library (refer to the 'timed' module).
"""
from pydantic import BaseModel, PrivateAttr
from threading import RLock
from typing import Dict, List
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .util import PP, Dirs, Now, str_to_dt, dt_to_str, DateTime2
from .action import Action
from .program import Program, ProgramItem
from .scheduler import Scheduler, TimedScheduler, ThresholdScheduler, Immediately
from .timed import Timed
from .resolver import resolve_action, resolve_scheduler, resolve_program
from .executor import Executor

logger = logging.getLogger(__name__)


class Dispatcher(BaseModel):
    """
    Serializations of this class are stored in the local file system. When a runtime starts
    up, Dispatch loads the last saved version.
    """

    actions: Dict[str, Action] = {}
    schedulers: Dict[str, Scheduler] = {}
    programs: Dict[str, Program] = {}
    scheduled_actions: Dict[str, List[str]] = {}
    deferred_scheduled_actions: Dict[str, Dict[str, List[str]]] = {}
    expiring_scheduled_actions: Dict[str, Dict[str, List[str]]] = {}
    deferred_scheduled_programs: Dict[str, Dict[str, List[DateTime2]]] = {}
    saved_dir: Optional[str] = None

    # not treated as a model attrs
    _timed: Timed = PrivateAttr(default_factory=Timed.get)
    _timed_for_out_of_band: Timed = PrivateAttr(default_factory=Timed)

    # jobs and timed object
    def set_timed(self, timed: Timed):
        self._timed = timed

    def run_jobs(self):
        return self._timed.run()

    def stop_jobs(self):
        return self._timed.stop()

    def jobs_are_running(self):
        return self._timed.is_running()

    def job_count(self):
        return self._timed.job_count()

    def clear_jobs(self):
        self._timed.clear()

    # internal dispatcher state access
    def get_actions(self):
        with Lok.lock:
            return self.actions

    def get_schedulers(self):
        with Lok.lock:
            return self.schedulers

    def get_programs(self):
        with Lok.lock:
            return self.programs

    def get_scheduled_actions(self):
        with Lok.lock:
            return self.scheduled_actions

    def get_deferred_scheduled_actions(self):
        with Lok.lock:
            return self.deferred_scheduled_actions

    def get_expiring_scheduled_actions(self):
        with Lok.lock:
            return self.expiring_scheduled_actions

    def get_deferred_scheduled_programs(self):
        with Lok.lock:
            return self.deferred_scheduled_programs

    def get_saved_dir(self):
        return self.saved_dir

    def get_actions_for_scheduler(self, scheduler_name: str):
        with Lok.lock:
            action_names = self.scheduled_actions[scheduler_name]
            return {
                action_name: self.actions[action_name] for action_name in action_names
            }

    # other internal dispatcher operations
    def check_for_expirations_and_deferrals(self):
        self.check_for_deferred_programs()
        self.check_for_deferred_actions()
        self.check_for_expiring_actions()

    def initialize(self):
        Lok.reset()
        self._timed_for_out_of_band.clear()
        self._timed_for_out_of_band.every(1).second.do(
            self.check_for_expirations_and_deferrals
        ).tag("check_for_expirations_and_deferrals")
        self._timed_for_out_of_band.run()

    def pprint(self):
        PP.pprint(self.dict())

    def load_current(self):
        return self.load_from_name("current")

    def save_current(self):
        with Lok.lock:
            self.save_to_name("current")

    def load_from_name(self, name: str):
        with Lok.lock:
            if self.saved_dir:
                with open(self.saved_dir + name + ".json", "r") as infile:
                    json_string = json.load(infile)
                    dictionary = json.loads(json_string)
                    return Dispatcher.resolve(dictionary)
            else:
                return None

    def save_to_name(self, name: str):
        with Lok.lock:
            if self.saved_dir:
                with open(self.saved_dir + name + ".json", "w") as outfile:
                    json.dump(self.json(), outfile, indent=2)

    def set_saved_dir(self, saved_dir: str):
        with Lok.lock:
            if saved_dir:
                if not os.path.exists(saved_dir):
                    os.makedirs(saved_dir)
            self.saved_dir = saved_dir
            self.save_current()

    def clear_all(self, should_save: bool = True):
        """
        Removes all actions, schedulers, programs, and foreground
        Timed instance jobs.
        """
        with Lok.lock:
            self.scheduled_actions.clear()
            self.deferred_scheduled_actions.clear()
            self.expiring_scheduled_actions.clear()
            self.deferred_scheduled_programs.clear()
            self.actions.clear()
            self.schedulers.clear()
            self.programs.clear()
            self._timed.clear()
            if should_save:
                self.save_current()

    def replace_all(self, replacement: object):
        """
        Note #1: the assumption is that the replacement is a Dispatcher. There's
        an module import circularity somewhere. Have yet to find a solution beyond
        this one. This will suffice for now. The submethod is there to show
        intention.

        1. except for the saved_dir, clear everything first
        2. replace elements with replacement elements
        3. save

        Note #2: after [1] all previous actions and schedules are no longer in existence.
        If processing should continue, invoke reschedule_all_schedulers() after
        invoking this method.
        """

        def typed_replace_all(replacement: Dispatcher):
            with Lok.lock:
                self.clear_all(should_save=False)
                self.actions = replacement.get_actions()
                self.schedulers = replacement.get_schedulers()
                self.scheduled_actions = replacement.get_scheduled_actions()
                self.deferred_scheduled_actions = (
                    replacement.get_deferred_scheduled_actions()
                )
                self.expiring_scheduled_actions = (
                    replacement.get_expiring_scheduled_actions()
                )
                self.deferred_scheduled_programs = (
                    replacement.get_deferred_scheduled_programs()
                )
                self.save_current()

        typed_replace_all(replacement)

    def describe_all(self):
        """
        Returns descriptions of all actions, schedulers and programs.
        """
        result = {}

        stuff = self.actions.copy()
        for name in stuff:
            stuff[name] = stuff[name].description()
        result["actions"] = stuff

        stuff = self.schedulers.copy()
        for name in stuff:
            stuff[name] = stuff[name].description()
        result["schedulers"] = stuff

        stuff = self.programs.copy()
        for name in stuff:
            stuff[name] = stuff[name].description()
        result["programs"] = stuff

        return result

    # actions
    def get_action(self, action_name: str):
        with Lok.lock:
            return self.actions.get(action_name, None)

    def describe_action(self, action_name: str):
        with Lok.lock:
            action = self.get_action(action_name)
            return (
                action.description()
                if action
                else f"action ({action_name}) does not exist."
            )

    def add_action(self, action_name: str, action: Action):
        with Lok.lock:
            assert (
                not action_name in self.actions
            ), f"action ({action_name}) already exists"
            self.actions[action_name] = action
            self.save_current()

    def set_action(self, action_name: str, action: Action):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            self.actions[action_name] = action
            self.save_current()

    def delete_action(self, action_name: str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            for scheduler_name in self.schedulers:
                action_names = self.scheduled_actions[scheduler_name]
                if action_name in action_names:
                    action_names.remove(action_name)
                self.check_scheduler(scheduler_name)
            self.actions.pop(action_name, None)
            self.save_current()

    def execute_action(self, action_name: str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            return self.get_action(action_name).execute()

    def execute_action_with_data(self, action_name: str, data: dict):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            return self.get_action(action_name).execute(data=data)

    def execute_supplied_action(self, supplied_action: Action):
        with Lok.lock:
            return supplied_action.execute()

    # schedulers
    def get_scheduler(self, scheduler_name: str):
        with Lok.lock:
            return self.schedulers.get(scheduler_name, None)

    def describe_scheduler(self, scheduler_name: str):
        with Lok.lock:
            scheduler = self.get_scheduler(scheduler_name)
            return (
                scheduler.description()
                if scheduler
                else f"scheduler ({scheduler_name}) does not exist."
            )

    def add_scheduler(self, scheduler_name: str, scheduler: Scheduler):
        with Lok.lock:
            assert (
                not scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) already exists"
            self.schedulers[scheduler_name] = scheduler
            self.scheduled_actions[scheduler_name] = []
            self.save_current()

    def set_scheduler(self, scheduler_name: str, scheduler: Scheduler):
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            self.schedulers[scheduler_name] = scheduler
            self.reschedule_scheduler(scheduler_name)
            self.save_current()

    def delete_scheduler(self, scheduler_name: str):
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            self.unschedule_scheduler(scheduler_name)
            self.schedulers.pop(scheduler_name)
            self.scheduled_actions[
                scheduler_name
            ].clear()  # pro-actively clean up. less work for GC.
            self.scheduled_actions.pop(scheduler_name)
            self.save_current()

    def check_scheduler(self, scheduler_name: str):
        assert (
            scheduler_name in self.schedulers
        ), f"scheduler ({scheduler_name}) does not exist"
        if len(self.scheduled_actions[scheduler_name]) == 0:
            scheduler = self.get_scheduler(scheduler_name)
            if isinstance(scheduler, TimedScheduler):
                scheduler.set_timed(self._timed)
            scheduler.unschedule(scheduler_name)

    # programs
    def get_program(self, program_name: str):
        with Lok.lock:
            return self.programs.get(program_name, None)

    def describe_program(self, program_name: str):
        with Lok.lock:
            program = self.get_program(program_name)
            return (
                program.description()
                if program
                else f"program ({program_name}) does not exist."
            )

    def add_program(self, program_name: str, program: Program):
        with Lok.lock:
            assert (
                not program_name in self.programs
            ), f"program ({program_name}) already exists"
            self.check_program(program)
            self.programs[program_name] = program
            self.save_current()

    def set_program(self, program_name: str, program: Program):
        with Lok.lock:
            assert (
                program_name in self.programs
            ), f"program ({program_name}) does not exist"
            self.check_program(program)
            self.programs[program_name] = program
            self.save_current()

    def delete_program(self, program_name: str):
        """
        Deletes program from programs and removes all references
        in deferred_scheduled_programs.
        """
        with Lok.lock:
            assert (
                program_name in self.programs
            ), f"program ({program_name}) does not exist"
            self.unschedule_program(program_name)
            self.programs.pop(program_name)
            self.save_current()

    def unschedule_program(self, program_name: str):
        """
        Deletes program from programs and removes all references
        in deferred_scheduled_programs.
        """
        with Lok.lock:
            assert (
                program_name in self.programs
            ), f"program ({program_name}) does not exist"
            to_remove = []
            deferred_scheduled_programs = self.deferred_scheduled_programs
            for wait_until_str in deferred_scheduled_programs:
                wait_until_programs = deferred_scheduled_programs[wait_until_str]
                if program_name in wait_until_programs:
                    wait_until_programs.pop(program_name)
                    if len(wait_until_programs) == 0:
                        to_remove.append(wait_until_str)
            for wait_until_str in to_remove:
                deferred_scheduled_programs.pop(wait_until_str)
            self.save_current()

    def check_program(self, program: Program):
        """
        Makes sure that actions and schedulers referenced in the program exist.
        """
        with Lok.lock:
            program_items = program.compute_program_items()
            error_msgs = []
            if len(program_items) == 0:
                error_msgs.append(f"empty program")
            else:
                for item in program_items:
                    if item.action_name not in self.actions:
                        error_msgs.append(f"missing action: ({item.action_name})")
                    if item.scheduler_name not in self.schedulers:
                        error_msgs.append(f"missing scheduler: ({item.scheduler_name})")
            if len(error_msgs) > 0:
                raise ValueError(", ".join(error_msgs))

    def schedule_program(self, program_name: str, start: datetime, stop: datetime):
        """
        This method defers the scheduling of a program by populating a dictionary.

        This dictionary (deferred_scheduled_programs) has a structure similar to
        deferred_scheduled_actions, except that the leaf arrays contain Datetime2
        instances instead of Actions.
        """
        with Lok.lock:
            assert (
                program_name in self.programs
            ), f"program ({program_name}) does not exist"
            program = self.programs[program_name]
            self.check_program(program)
            # needs to be a str key because of Dispatcher json serialization and deserialization
            wait_until_str = dt_to_str(start)
            if wait_until_str not in self.deferred_scheduled_programs:
                # initialize the key's value
                self.deferred_scheduled_programs[wait_until_str] = {}
            # same structure as scheduled_actions
            deferred_programs = self.deferred_scheduled_programs[wait_until_str]
            if program_name not in deferred_programs:
                deferred_programs[program_name] = []  # initialize list of DateTime2s
            datetime2s = deferred_programs[program_name]
            datetime2 = DateTime2(dt1=start, dt2=stop)
            assert (
                datetime2 not in datetime2s
            ), f"({program_name}) already scheduled using start ({start}), ({stop})"
            datetime2s.append(datetime2)
            self.save_current()

    def check_for_deferred_programs(self):
        """
        This gets run as a job in the out-of-band Timed instance.

        It looks for deferred programs whose start dates are prior to the current
        time and 'disseminates' these programs. See the
        schedule_program and initialize methods for more details.
        """
        with Lok.lock:
            now = Now.dt()
            to_remove = []
            for wait_until_str in self.deferred_scheduled_programs:
                wait_until = str_to_dt(wait_until_str)
                if wait_until < now:
                    deferred_programs = self.deferred_scheduled_programs[wait_until_str]
                    for program_name in deferred_programs:
                        for datetime2 in deferred_programs[program_name]:
                            start, stop = datetime2.dt1, datetime2.dt2
                            try:
                                self.disseminate_program(program_name, start, stop)
                            except Exception as exception:
                                logger.error(
                                    f"failed to dissemminate program ({program_name}) using start ({start}), ({stop})",
                                    exception,
                                )
                    to_remove.append(wait_until_str)
            for wait_until_str in to_remove:  # modify outside the previous for-loop
                self.deferred_scheduled_programs.pop(wait_until_str)
            self.save_current()

    def disseminate_program(self, program_name: str, start: datetime, stop: datetime):
        """
        Defers and expires scheduler/actions as necessary. Once disseminated,
        the associated scheduler/actions are dissassociated from the originating
        program. The chickens have flown the coop. They are now scheduled and running
        independently.
        """
        with Lok.lock:
            assert (
                program_name in self.programs
            ), f"program ({program_name}) does not exist"
            program = self.programs[program_name]
            self.check_program(program)
            program_items = program.compute_program_items(start, stop)
            for item in program_items:
                if item.type == "defer":
                    self.defer_action(item.scheduler_name, item.action_name, item.dt)
                elif item.type == "expire":
                    self.expire_action(item.scheduler_name, item.action_name, item.dt)

    def get_deferred_program_count(self):
        # returns the total number of datetime2s in the deferred programs dictionary (a dictionary
        # of dictionaries)
        with Lok.lock:
            result = 0
            for deferred_programs in self.deferred_scheduled_programs.values():
                result += sum(
                    len(datetime2_array)
                    for datetime2_array in deferred_programs.values()
                )
            return result

    def clear_all_deferred_programs(self):
        with Lok.lock:
            self.deferred_scheduled_programs.clear()
            self.save_current()

    # scheduling
    def schedule_action(self, scheduler_name: str, action_name: str):
        """
        Puts the scheduler/action into active processing. The scheduled_action
        dictionary mirrors the successful scheduling of actions.
        """
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            assert not action_name in self.scheduled_actions[scheduler_name]
            scheduler = self.get_scheduler(scheduler_name)
            if isinstance(scheduler, TimedScheduler):
                scheduler.set_timed(self._timed)
            elif isinstance(
                scheduler, Immediately
            ):  # executes once; does not participate further in scheduling
                self.get_action(action_name).execute()
                return
            self.scheduled_actions[scheduler_name].append(action_name)
            if len(self.scheduled_actions[scheduler_name]) == 1:
                scheduler.schedule(
                    scheduler_name, Executor(self.get_actions_for_scheduler)
                )  # have an action to trigger
            self.save_current()

    def unschedule_scheduler_action(self, scheduler_name: str, action_name: str):
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            # get the scheduler
            scheduler = self.get_scheduler(scheduler_name)
            if isinstance(scheduler, TimedScheduler):
                scheduler.set_timed(self._timed)
            # remove the action from the scheduler's actions
            action_names = self.scheduled_actions[scheduler_name]
            if action_name in action_names:
                action_names.remove(action_name)
            # unschedule the scheduler if there are no associated actions
            if len(action_names) == 0:
                scheduler.unschedule(scheduler_name)
            self.save_current()

    def unschedule_scheduler(self, scheduler_name: str):
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            scheduler = self.get_scheduler(scheduler_name)
            if isinstance(scheduler, TimedScheduler):
                scheduler.set_timed(self._timed)
            scheduler.unschedule(scheduler_name)
            self.scheduled_actions[scheduler_name].clear()
            self.save_current()

    def reschedule_scheduler(self, scheduler_name: str):
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            scheduler = self.get_scheduler(scheduler_name)
            if isinstance(scheduler, TimedScheduler):
                scheduler.set_timed(self._timed)
            scheduler.schedule(scheduler_name, Executor(self.get_actions_for_scheduler))

    def reschedule_all_schedulers(self):
        with Lok.lock:
            for scheduler_name in self.scheduled_actions:
                self.reschedule_scheduler(scheduler_name)

    def get_scheduled_action_count(self):
        # returns the total number of actions in the scheduled_actions dictionary
        # should be equal to the number of jobs in related Timed instance
        with Lok.lock:
            return sum(
                len(action_array) for action_array in self.scheduled_actions.values()
            )

    # defer scheduler/action
    def defer_action(self, scheduler_name: str, action_name: str, wait_until: datetime):
        """
        This method defers the start of scheduling an action. The data structure is a dictionary
        with a datetime as the key and a scheduled_actions style dictionary as the value.
        """
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            # needs to be a str key because of Dispatcher json serialization and deserialization
            wait_until_str = dt_to_str(wait_until)
            if wait_until_str not in self.deferred_scheduled_actions:
                # initialize the key's value
                self.deferred_scheduled_actions[wait_until_str] = {}
            # same structure as scheduled_actions
            scheduled_actions = self.deferred_scheduled_actions[wait_until_str]
            if scheduler_name not in scheduled_actions:
                scheduled_actions[scheduler_name] = []  # initialize list of Actions
            deferred_actions = scheduled_actions[scheduler_name]
            assert (
                action_name not in deferred_actions
            ), f"({action_name}) already scheduled using ({scheduler_name}) as of ({wait_until_str})"
            deferred_actions.append(action_name)
            self.save_current()

    def check_for_deferred_actions(self):
        """
        This gets run as a job in the out-of-band Timed instance.

        It looks for deferred actions whose dates are prior to the current
        time and schedules them using the associated scheduler. See the
        defer_action and initialize methods for more details.
        """
        with Lok.lock:
            now = Now.dt()
            to_remove = []
            for wait_until_str in self.deferred_scheduled_actions:
                wait_until = str_to_dt(wait_until_str)
                if wait_until < now:
                    scheduled_actions = self.deferred_scheduled_actions[wait_until_str]
                    for scheduler_name in scheduled_actions:
                        for action_name in scheduled_actions[scheduler_name]:
                            try:
                                self.schedule_action(scheduler_name, action_name)
                            except Exception as exception:
                                logger.error(
                                    f"failed to schedule deferred action ({action_name}) under ({scheduler_name}) as of ({wait_until_str})",
                                    exception,
                                )
                    to_remove.append(wait_until_str)
            for wait_until_str in to_remove:  # modify outside the previous for-loop
                self.deferred_scheduled_actions.pop(wait_until_str)
            self.save_current()

    def get_deferred_action_count(self):
        # returns the total number of actions in the deferred actions dictionary (a dictionary
        # of dictionaries)
        with Lok.lock:
            result = 0
            for scheduled_actions in self.deferred_scheduled_actions.values():
                result += sum(
                    len(action_array) for action_array in scheduled_actions.values()
                )
            return result

    def clear_all_deferred_actions(self):
        with Lok.lock:
            self.deferred_scheduled_actions.clear()
            self.save_current()

    # expire scheduler/action
    def expire_action(self, scheduler_name: str, action_name: str, expire_on: datetime):
        """
        This method expires an action with scheduler. The data structure is a dictionary
        with a datetime as the key and a scheduled_actions style dictionary as the value.
        """
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            # needs to be a str key because of Dispatcher json serialization and deserialization
            expire_on_str = dt_to_str(expire_on)
            if expire_on_str not in self.expiring_scheduled_actions:
                # initialize the key's value
                self.expiring_scheduled_actions[expire_on_str] = {}
            # same structure as scheduled_actions
            scheduled_actions = self.expiring_scheduled_actions[expire_on_str]
            if scheduler_name not in scheduled_actions:
                scheduled_actions[scheduler_name] = []  # initialize list of Actions
            expiring_actions = scheduled_actions[scheduler_name]
            assert (
                action_name not in expiring_actions
            ), f"({action_name}) already scheduled for expiration under ({scheduler_name}) as of ({expire_on_str})"
            expiring_actions.append(action_name)
            self.save_current()

    def check_for_expiring_actions(self):
        """
        This gets run as a job in the out-of-band Timed instance.

        It looks for expiring actions whose dates are later than the current
        time and unschedules them within the context of the associated scheduler.
        See the expire_action and initialize methods for more details.
        """
        with Lok.lock:
            now = Now.dt()
            to_remove = []
            for expire_on_str in self.expiring_scheduled_actions:
                expire_on = str_to_dt(expire_on_str)
                if expire_on < now:
                    scheduled_actions = self.expiring_scheduled_actions[expire_on_str]
                    for scheduler_name in scheduled_actions:
                        for action_name in scheduled_actions[scheduler_name]:
                            try:
                                self.unschedule_scheduler_action(
                                    scheduler_name, action_name
                                )
                            except Exception as exception:
                                logger.error(
                                    f"failed to unschedule action ({action_name}) under ({scheduler_name}) as of ({expire_on_str})",
                                    exception,
                                )
                    to_remove.append(expire_on_str)
            for expire_on_str in to_remove:  # modify outside the previous for-loop
                self.expiring_scheduled_actions.pop(expire_on_str)
            self.save_current()

    def get_expiring_action_count(self):
        # returns the total number of actions in the deferred actions dictionary (a dictionary
        # of dictionaries)
        with Lok.lock:
            result = 0
            for scheduled_actions in self.expiring_scheduled_actions.values():
                result += sum(
                    len(action_array) for action_array in scheduled_actions.values()
                )
            return result

    def clear_all_expiring_actions(self):
        with Lok.lock:
            self.expiring_scheduled_actions.clear()
            self.save_current()

    # utility
    def scheduler_tag(self, scheduler_name: str, action_name: str):
        # computes job tag for scheduler and action
        return f"{scheduler_name}:{action_name}"

    @classmethod
    def resolve(cls, dictionary: dict = {}):
        """
        converts dictionary to an Dispatcher instance.
        """
        if len(dictionary) == 0:
            return Dispatcher()
        else:
            saved_dir = dictionary["saved_dir"]
            actions = dictionary["actions"]
            schedulers = dictionary["schedulers"]
            programs = dictionary["programs"]
            scheduled_actions = dictionary["scheduled_actions"]
            deferred_scheduled_actions = dictionary["deferred_scheduled_actions"]
            expiring_scheduled_actions = dictionary["expiring_scheduled_actions"]
            deferred_scheduled_programs = dictionary["deferred_scheduled_programs"]
            # replace key's value for each key...
            for action_name in actions:
                actions[action_name] = resolve_action(actions[action_name])
            for scheduler_name in schedulers:
                schedulers[scheduler_name] = resolve_scheduler(
                    schedulers[scheduler_name]
                )
            for program_name in programs:
                programs[program_name] = resolve_program(programs[program_name])
            return Dispatcher(
                saved_dir=saved_dir,
                actions=actions,
                schedulers=schedulers,
                programs=programs,
                scheduled_actions=scheduled_actions,
                deferred_scheduled_actions=deferred_scheduled_actions,
                deferred_scheduled_programs=deferred_scheduled_programs,
            )


class Lok:
    """
    usage:
        with Lok.lock:
            # critical section
    note:
        singleton
    """

    lock = RLock()

    @classmethod
    def reset(cls):
        cls.lock = RLock()


class DispatcherSingleton:
    # this call returns the standard non-test Data singleton
    dispatcher = None

    @classmethod
    def get(cls):
        if not cls.dispatcher:
            cls.dispatcher = Dispatcher(saved_dir=Dirs.saved_dir())
            try:
                cls.dispatcher = cls.dispatcher.load_current()
            except Exception as exception:
                logger.error("error loading dispatcher from disk", exception)
            cls.dispatcher.set_timed(Timed.get())
            cls.dispatcher.initialize()
            cls.dispatcher.reschedule_all_schedulers()
        return cls.dispatcher
