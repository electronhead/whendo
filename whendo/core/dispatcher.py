"""
This class implements a single process-based system for defining and scheduling actions local
to the python runtime (api server, testing harness). The class implements all of the potential
endpoints of a restful api and supports testing outside of the restful api implementation.

Instances of this class contain Schedulers and Actions, which can at any point be submitted to and removed from the
job scheduling mechanism of the schedule library (refer to the 'continuous' module).
"""
from pydantic import BaseModel, PrivateAttr
from threading import RLock
from typing import Dict, List
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .util import PP, Dirs, DateTime, Now, str_to_dt, dt_to_str
from .action import Action
from .program import Program
from .scheduler import Scheduler
from .continuous import Continuous
from .resolver import resolve_action, resolve_scheduler, resolve_program

logger = logging.getLogger(__name__)


class Dispatcher(BaseModel):
    """
    Serializations of this class are stored in the local file system. When a runtime starts
    up, Dispatch loads the last saved version.
    """

    actions: Dict[str, Action] = {}
    schedulers: Dict[str, Scheduler] = {}
    programs: Dict[str, Program] = {}
    schedulers_actions: Dict[str, List[str]] = {}
    deferred_schedulers_actions: Dict[str, Dict[str, List[str]]] = {}
    expired_schedulers_actions: Dict[str, Dict[str, List[str]]] = {}
    saved_dir: Optional[str] = None

    # not treated as a model attrs
    _continuous: Continuous = PrivateAttr(default_factory=Continuous.get)
    _continuous_for_out_of_band: Continuous = PrivateAttr(default_factory=Continuous)

    # jobs and continuous object
    def get_continuous(self):
        return self._continuous

    def set_continuous(self, continuous: Continuous):
        self._continuous = continuous

    def run_jobs(self):
        self._continuous.run_continuously()

    def stop_jobs(self):
        self._continuous.stop_running_continuously()

    def jobs_are_running(self):
        return self._continuous.is_running()

    def job_count(self):
        return self._continuous.job_count()

    def clear_jobs(self):
        self._continuous.clear()

    def get_continuous_for_out_of_band(self):
        return self._continuous_for_out_of_band

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

    def get_schedulers_actions(self):
        with Lok.lock:
            return self.schedulers_actions

    def get_deferred_schedulers_actions(self):
        with Lok.lock:
            return self.deferred_schedulers_actions

    def get_expired_schedulers_actions(self):
        with Lok.lock:
            return self.expired_schedulers_actions

    def get_saved_dir(self):
        return self.saved_dir

    # other internal dispatcher operations
    def initialize(self):
        Lok.reset()
        self._continuous_for_out_of_band.clear()
        self._continuous_for_out_of_band.every(1).second.do(
            self.check_for_deferred_actions
        ).tag("deferred")
        self._continuous_for_out_of_band.every(1).second.do(
            self.check_for_expired_actions
        ).tag("expired")
        self._continuous_for_out_of_band.run_continuously()

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
        Removes all actions and schedulers and programs and terminates their involvement
        with job processing.
        """
        with Lok.lock:
            schedulers_copy = self.schedulers.copy()
            for scheduler_name in schedulers_copy:
                self.delete_scheduler(scheduler_name)

            actions_copy = self.actions.copy()
            for action_name in actions_copy:
                self.delete_action(action_name)

            programs_copy = self.programs.copy()
            for program_name in programs_copy:
                self.delete_program(program_name)

            self.schedulers_actions.clear()
            self.deferred_schedulers_actions.clear()
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
                self.schedulers_actions = replacement.get_schedulers_actions()
                self.deferred_schedulers_actions = (
                    replacement.get_deferred_schedulers_actions()
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
            self.reschedule_action(action_name)
            self.save_current()

    def delete_action(self, action_name: str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            for scheduler_name in self.schedulers:
                self.unschedule_action(action_name)
                action_names = self.schedulers_actions[scheduler_name]
                if action_name in action_names:
                    action_names.remove(action_name)
            self.actions.pop(action_name, None)
            self.save_current()

    def execute_action(self, action_name: str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            return self.get_action(action_name).execute()

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
            self.schedulers_actions[scheduler_name] = []
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
            self.schedulers_actions[
                scheduler_name
            ].clear()  # pro-actively clean up. less work for GC.
            self.schedulers_actions.pop(scheduler_name)
            self.save_current()

    def execute_scheduler_actions(self, scheduler_name: str):
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            result = []
            for action_name in self.schedulers_actions.get(scheduler_name, []):
                result.append(self.get_action(action_name).execute())
            return result

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
        with Lok.lock:
            assert (
                program_name in self.programs
            ), f"program ({program_name}) does not exist"
            self.programs.pop(program_name)
            self.save_current()

    def check_program(self, program: Program):
        error_msgs = []

        # check action names
        action_names = set(
            (
                x
                for x in [program.prologue_name, program.epilogue_name]
                if x != "NOT_APPLICABLE"
            )
        )
        for scheduler_name in program.body:
            action_names.update(program.body[scheduler_name])
        missing_actions = action_names - set(self.actions.keys())
        if len(missing_actions) > 0:
            error_msgs.append(f"actions missing: ({missing_actions})")

        # check scheduler names
        scheduler_names = {"immediately"}
        scheduler_names.update(set(program.body.keys()))
        missing_schedulers = scheduler_names - set(self.schedulers.keys())
        if len(missing_schedulers) > 0:
            error_msgs.append(f"schedulers missing: ({missing_schedulers})")

        if len(error_msgs) > 0:
            raise ValueError(", ".join(error_msgs))

    def schedule_program(self, program_name: str, start: datetime, stop: datetime):
        """
        This method utilizes the named Program's innards and schedules actions
        specified therein.
        """
        with Lok.lock:
            assert (
                program_name in self.get_programs()
            ), f"program ({program_name}) does not exist"

            program = self.get_program(program_name)
            self.check_program(program)

            if program.prologue_name != "NOT_APPLICABLE":
                self.defer_action("immediately", program.prologue_name, start)

            if len(program.body) > 0:
                timedelta_offset = timedelta(seconds=program.offset_seconds)
                start_plus = start + timedelta_offset
                stop_minus = stop - timedelta_offset
                for scheduler_name in program.body:
                    for action_name in program.body[scheduler_name]:
                        self.defer_action(scheduler_name, action_name, start_plus)
                        self.expire_action(scheduler_name, action_name, stop_minus)

            if program.epilogue_name != "NOT_APPLICABLE":
                self.defer_action("immediately", program.epilogue_name, stop)

            self.save_current()

    # scheduling
    def schedule_action(self, scheduler_name: str, action_name: str):
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            assert not action_name in self.schedulers_actions[scheduler_name]
            scheduler = self.get_scheduler(scheduler_name)
            action = self.actions.get(action_name)
            tag = self.scheduler_tag(scheduler_name, action_name)
            scheduler.schedule_action(tag, action, self._continuous)
            if scheduler.joins_schedulers_actions():
                self.schedulers_actions[scheduler_name].append(action_name)
                self.save_current()

    def unschedule_action(self, action_name: str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            for scheduler_name in self.schedulers_actions:
                if action_name in self.schedulers_actions[scheduler_name]:
                    tag = self.scheduler_tag(scheduler_name, action_name)
                    self._continuous.clear(tag)
                    action_names = self.schedulers_actions[scheduler_name]
                    if action_name in action_names:
                        action_names.remove(action_name)
            self.save_current()

    def unschedule_scheduler_action(self, scheduler_name: str, action_name: str):
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            tag = self.scheduler_tag(scheduler_name, action_name)
            self._continuous.clear(tag)
            action_names = self.schedulers_actions[scheduler_name]
            if action_name in action_names:
                action_names.remove(action_name)
                self.save_current()

    def reschedule_action(self, action_name: str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            for scheduler_name in self.schedulers_actions:
                if action_name in self.schedulers_actions[scheduler_name]:
                    tag = self.scheduler_tag(scheduler_name, action_name)
                    self._continuous.clear(tag)
                    scheduler = self.get_scheduler(scheduler_name)
                    action = self.actions[action_name]
                    scheduler.schedule_action(tag, action, self._continuous)

    def unschedule_scheduler(self, scheduler_name: str):
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            for action_name in self.schedulers_actions[scheduler_name]:
                tag = self.scheduler_tag(scheduler_name, action_name)
                self._continuous.clear(tag)
            self.schedulers_actions[scheduler_name].clear()
            self.save_current()

    def reschedule_scheduler(self, scheduler_name: str):
        with Lok.lock:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"
            scheduler_actions = self.schedulers_actions[scheduler_name]
            for action_name in scheduler_actions:
                tag = self.scheduler_tag(scheduler_name, action_name)
                self._continuous.clear(tag)
                scheduler = self.get_scheduler(scheduler_name)
                action = self.actions[action_name]
                scheduler.schedule_action(tag, action, self._continuous)

    def reschedule_all_schedulers(self):
        with Lok.lock:
            for scheduler_name in self.schedulers_actions:
                for action_name in self.schedulers_actions[scheduler_name]:
                    tag = self.scheduler_tag(scheduler_name, action_name)
                    self._continuous.clear(tag)
                    scheduler = self.get_scheduler(scheduler_name)
                    action = self.actions[action_name]
                    scheduler.schedule_action(tag, action, self._continuous)

    def get_scheduled_action_count(self):
        # returns the total number of actions in the schedulers_actions dictionary
        # should be equal to the number of jobs in related Continuous instance
        with Lok.lock:
            return sum(
                len(action_array) for action_array in self.schedulers_actions.values()
            )

    # defer scheduler/action
    def defer_action(self, scheduler_name: str, action_name: str, wait_until: datetime):
        """
        This method defers the start of scheduling an action. The data structure is a dictionary
        with a datetime as the key and a schedulers_actions style dictionary as the value.
        """
        with Lok.lock:
            assert (
                scheduler_name in self.get_schedulers()
            ), f"scheduler ({scheduler_name}) does not exist"
            assert (
                action_name in self.get_actions()
            ), f"action ({action_name}) does not exist"
            # needs to be a str key because of Dispatcher json serialization and deserialization
            wait_until_str = dt_to_str(wait_until)
            if wait_until_str not in self.deferred_schedulers_actions:
                # initialize the key's value
                self.deferred_schedulers_actions[wait_until_str] = {}
            # same structure as schedulers_actions
            schedulers_actions = self.deferred_schedulers_actions[wait_until_str]
            if scheduler_name not in schedulers_actions:
                schedulers_actions[scheduler_name] = []  # initialize list of Actions
            deferred_actions = schedulers_actions[scheduler_name]
            assert (
                action_name not in deferred_actions
            ), f"({action_name}) already scheduled using ({scheduler_name}) as of ({wait_until_str})"
            deferred_actions.append(action_name)
            self.save_current()

    def check_for_deferred_actions(self):
        """
        This gets run as a job in the out-of-band Continuous instance.

        It looks for deferred actions whose dates are prior to the current
        time and schedules them using the associated scheduler. See the
        defer_action and initialize methods for more details.
        """
        with Lok.lock:
            now = Now.dt()
            to_remove = []
            for wait_until_str in self.deferred_schedulers_actions:
                wait_until = str_to_dt(wait_until_str)
                if wait_until < now:
                    schedulers_actions = self.deferred_schedulers_actions[
                        wait_until_str
                    ]
                    for scheduler_name in schedulers_actions:
                        for action_name in schedulers_actions[scheduler_name]:
                            try:
                                self.schedule_action(
                                    scheduler_name=scheduler_name,
                                    action_name=action_name,
                                )
                            except Exception as exception:
                                logger.error(
                                    f"failed to schedule deferred action ({action_name}) under ({scheduler_name}) as of ({wait_until_str})",
                                    exception,
                                )
                    to_remove.append(wait_until_str)
            for wait_until_str in to_remove:  # modify outside the previous for-loop
                self.deferred_schedulers_actions.pop(wait_until_str)
            self.save_current()

    def get_deferred_action_count(self):
        # returns the total number of actions in the deferred actions dictionary (a dictionary
        # of dictionaries)
        with Lok.lock:
            result = 0
            for schedulers_actions in self.deferred_schedulers_actions.values():
                result += sum(
                    len(action_array) for action_array in schedulers_actions.values()
                )
            return result

    def clear_all_deferred_actions(self):
        with Lok.lock:
            self.deferred_schedulers_actions.clear()
            self.save_current()

    # expire scheduler/action
    def expire_action(self, scheduler_name: str, action_name: str, expire_on: datetime):
        """
        This method expires an action with scheduler. The data structure is a dictionary
        with a datetime as the key and a schedulers_actions style dictionary as the value.
        """
        with Lok.lock:
            assert (
                scheduler_name in self.get_schedulers()
            ), f"scheduler ({scheduler_name}) does not exist"
            assert (
                action_name in self.get_actions()
            ), f"action ({action_name}) does not exist"
            # needs to be a str key because of Dispatcher json serialization and deserialization
            expire_on_str = dt_to_str(expire_on)
            if expire_on_str not in self.expired_schedulers_actions:
                # initialize the key's value
                self.expired_schedulers_actions[expire_on_str] = {}
            # same structure as schedulers_actions
            schedulers_actions = self.expired_schedulers_actions[expire_on_str]
            if scheduler_name not in schedulers_actions:
                schedulers_actions[scheduler_name] = []  # initialize list of Actions
            expired_actions = schedulers_actions[scheduler_name]
            assert (
                action_name not in expired_actions
            ), f"({action_name}) already scheduled for expiration under ({scheduler_name}) as of ({expire_on_str})"
            expired_actions.append(action_name)
            self.save_current()

    def check_for_expired_actions(self):
        """
        This gets run as a job in the out-of-band Continuous instance.

        It looks for expired actions whose dates are later than the current
        time and unschedules them within the context of the associated scheduler.
        See the expire_action and initialize methods for more details.
        """
        with Lok.lock:
            now = Now.dt()
            to_remove = []
            for expire_on_str in self.expired_schedulers_actions:
                expire_on = str_to_dt(expire_on_str)
                if expire_on < now:
                    schedulers_actions = self.expired_schedulers_actions[expire_on_str]
                    for scheduler_name in schedulers_actions:
                        for action_name in schedulers_actions[scheduler_name]:
                            try:
                                self.unschedule_scheduler_action(
                                    scheduler_name=scheduler_name,
                                    action_name=action_name,
                                )
                            except Exception as exception:
                                logger.error(
                                    f"failed to unschedule action ({action_name}) under ({scheduler_name}) as of ({expire_on_str})",
                                    exception,
                                )
                    to_remove.append(expire_on_str)
            for expire_on_str in to_remove:  # modify outside the previous for-loop
                self.expired_schedulers_actions.pop(expire_on_str)
            self.save_current()

    def get_expired_action_count(self):
        # returns the total number of actions in the deferred actions dictionary (a dictionary
        # of dictionaries)
        with Lok.lock:
            result = 0
            for schedulers_actions in self.expired_schedulers_actions.values():
                result += sum(
                    len(action_array) for action_array in schedulers_actions.values()
                )
            return result

    def clear_all_expired_actions(self):
        with Lok.lock:
            self.expired_schedulers_actions.clear()
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
            schedulers_actions = dictionary["schedulers_actions"]
            deferred_schedulers_actions = dictionary["deferred_schedulers_actions"]
            expired_schedulers_actions = dictionary["expired_schedulers_actions"]
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
                schedulers_actions=schedulers_actions,
                deferred_schedulers_actions=deferred_schedulers_actions,
                expired_schedulers_actions=expired_schedulers_actions,
            )


# ------------------
"""
usage:
  with Lok.lock:
    # critical section
note:
  singleton
"""


class Lok:
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
            cls.dispatcher.set_continuous(Continuous.get())
            cls.dispatcher.initialize()
            cls.dispatcher.reschedule_all_schedulers()
        return cls.dispatcher
