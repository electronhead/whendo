"""
This class implements a single process-based system for defining and scheduling actions local
to the python runtime (api server, testing harness). The class implements all of the potential
endpoints of a restful api and supports testing outside of the restful api implementation.

Instances of this class contain Schedulers, Actions and Programs, which can at any point be submitted to and removed from the
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
from .hooks import DispatcherHooks
from .action import Action
from .program import Program, ProgramItem
from .scheduler import Scheduler, TimedScheduler, ThresholdScheduler, Immediately
from .timed import Timed
from .resolver import resolve_action, resolve_scheduler, resolve_program
from .executor import Executor
from .scheduling import (
    DeferredPrograms,
    DeferredProgram,
    ScheduledActions,
    DatedScheduledActions,
)

logger = logging.getLogger(__name__)


class Dispatcher(BaseModel):
    """
    Serializations of this class are stored in the local file system. When a runtime starts
    up, Dispatch loads the last saved version.
    """

    actions: Dict[str, Action] = {}
    schedulers: Dict[str, Scheduler] = {}
    programs: Dict[str, Program] = {}
    scheduled_actions: ScheduledActions = ScheduledActions()
    deferred_scheduled_actions: DatedScheduledActions = DatedScheduledActions()
    expiring_scheduled_actions: DatedScheduledActions = DatedScheduledActions()
    deferred_programs: DeferredPrograms = DeferredPrograms()
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

    def get_deferred_programs(self):
        return self.deferred_programs

    def get_saved_dir(self):
        return self.saved_dir

    def get_actions_for_scheduler(self, scheduler_name: str):
        with Lok.lock:
            action_names = self.scheduled_actions.actions(scheduler_name)
            return {
                action_name: self.actions[action_name] for action_name in action_names
            }

    def unschedule_scheduler_thunk(self, scheduler_name: str):
        with Lok.lock:
            self.unschedule_scheduler(scheduler_name)

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
        DispatcherHooks.init(
            schedule_program_thunk=lambda program_name, start, stop: self.schedule_program(
                program_name, start, stop
            ),
            unschedule_program_thunk=lambda program_name: self.unschedule_program(
                program_name
            ),
            schedule_action_thunk=lambda scheduler_name, action_name: self.schedule_action(
                scheduler_name, action_name
            ),
            unschedule_scheduler_action_thunk=lambda scheduler_name, action_name: self.unschedule_scheduler_action(
                scheduler_name, action_name
            ),
            unschedule_scheduler_thunk=lambda scheduler_name, action_name: self.unschedule_scheduler(
                scheduler_name
            ),
            defer_action_thunk=lambda scheduler_name, action_name, wait_until: self.defer_action(
                scheduler_name, action_name, wait_until
            ),
            expire_action_thunk=lambda scheduler_name, action_name, expire_on: self.expire_action(
                scheduler_name, action_name, expire_on
            ),
            clear_all_deferred_actions_thunk=lambda scheduler_name, action_name, expire_on: self.clear_all_deferred_actions(),
            clear_all_expiring_actions_thunk=lambda scheduler_name, action_name, expire_on: self.clear_all_expiring_actions(),
        )

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
            self.deferred_programs.clear()
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
                self.deferred_programs = replacement.get_deferred_programs()
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
            self.check_action_name(action_name, invert=True)
            self.actions[action_name] = action
            self.save_current()

    def set_action(self, action_name: str, action: Action):
        with Lok.lock:
            self.check_action_name(action_name)
            self.actions[action_name] = action
            self.save_current()

    def delete_action(self, action_name: str):
        with Lok.lock:
            self.check_action_name(action_name)
            deleted_schedulers = self.scheduled_actions.delete_action(action_name)
            for ds in deleted_schedulers:
                self.check_scheduler(ds)
            self.actions.pop(action_name, None)
            self.deferred_scheduled_actions.delete_dated_action(action_name=action_name)
            self.expiring_scheduled_actions.delete_dated_action(action_name=action_name)

            # delete programs referencing action_name
            programs_copy = self.programs.copy()
            for program_name in programs_copy:
                program_items = programs_copy[program_name].compute_program_items()
                for program_item in program_items:
                    if program_item.action_name == action_name:
                        self.delete_program(program_name)
                        break

            self.save_current()

    def execute_action(self, action_name: str):
        with Lok.lock:
            self.check_action_name(action_name)
            return self.get_action(action_name).execute()

    def execute_action_with_data(self, action_name: str, data: dict):
        with Lok.lock:
            self.check_action_name(action_name)
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
            self.check_scheduler_name(scheduler_name, invert=True)
            self.schedulers[scheduler_name] = scheduler
            self.save_current()

    def set_scheduler(self, scheduler_name: str, scheduler: Scheduler):
        with Lok.lock:
            self.check_scheduler_name(scheduler_name)
            self.schedulers[scheduler_name] = scheduler
            self.reschedule_scheduler(scheduler_name)
            self.save_current()

    def delete_scheduler(self, scheduler_name: str):
        with Lok.lock:
            self.check_scheduler_name(scheduler_name)
            self.unschedule_scheduler(scheduler_name)
            self.schedulers.pop(scheduler_name)
            self.scheduled_actions.delete_scheduler(scheduler_name)
            self.deferred_scheduled_actions.delete_dated_scheduler(
                scheduler_name=scheduler_name
            )
            self.expiring_scheduled_actions.delete_dated_scheduler(
                scheduler_name=scheduler_name
            )

            # delete programs referencing scheduler_name
            programs_copy = self.programs.copy()
            for program_name in programs_copy:
                program_items = programs_copy[program_name].compute_program_items()
                for program_item in program_items:
                    if program_item.scheduler_name == scheduler_name:
                        self.delete_program(program_name)
                        break

            self.save_current()

    def check_scheduler(self, scheduler_name: str):
        self.check_scheduler_name(scheduler_name)
        if len(self.scheduled_actions.actions(scheduler_name)) == 0:
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
            self.check_program_name(program_name, invert=True)
            self.check_program(program)
            self.programs[program_name] = program
            self.save_current()

    def set_program(self, program_name: str, program: Program):
        with Lok.lock:
            self.check_program_name(program_name)
            self.check_program(program)
            self.programs[program_name] = program
            self.save_current()

    def delete_program(self, program_name: str):
        """
        Deletes program from programs and removes all references
        in deferred_scheduled_programs.
        """
        with Lok.lock:
            self.check_program_name(program_name)
            self.unschedule_program(program_name)
            self.programs.pop(program_name)
            self.save_current()

    def unschedule_program(self, program_name: str):
        """
        Deletes program from programs and removes all references
        in deferred_scheduled_programs.
        """
        with Lok.lock:
            self.check_program_name(program_name)
            self.deferred_programs.clear_program(program_name)
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
        This method defers the scheduling of a program.
        """
        with Lok.lock:
            self.check_program_name(program_name)
            program = self.programs[program_name]
            self.check_program(program)
            self.deferred_programs.add(DeferredProgram(program_name, start, stop))
            self.save_current()

    def check_for_deferred_programs(self):
        """
        This gets run as a job in the out-of-band Timed instance.

        It looks for deferred programs whose start dates are prior to the current
        time and 'disseminates' these programs. See the
        schedule_program and initialize methods for more details.
        """
        with Lok.lock:
            for dp in self.deferred_programs.pop():
                try:
                    self.disseminate_program(dp.program_name, dp.start, dp.stop)
                except Exception as exception:
                    logger.error(
                        f"failed to dissemminate program ({program_name}) using start ({start}), ({stop})",
                        exception,
                    )
                self.save_current()

    def disseminate_program(self, program_name: str, start: datetime, stop: datetime):
        """
        Defers and expires scheduler/actions as necessary. Once disseminated,
        the associated scheduler/actions are dissassociated from the originating
        program. The chickens have flown the coop. They are now scheduled and running
        independently.
        """
        with Lok.lock:
            self.check_program_name(program_name)
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
            return self.deferred_programs.count()

    def clear_all_deferred_programs(self):
        with Lok.lock:
            self.deferred_programs.clear()
            self.save_current()

    # scheduling
    def schedule_action(self, scheduler_name: str, action_name: str):
        """
        Puts the scheduler/action into active processing. The scheduled_action
        dictionary mirrors the successful scheduling of actions.
        """
        with Lok.lock:
            self.check_scheduler_name(scheduler_name)
            self.check_action_name(action_name)
            scheduler = self.get_scheduler(scheduler_name)
            if isinstance(scheduler, TimedScheduler):
                scheduler.set_timed(self._timed)
            elif isinstance(
                scheduler, Immediately
            ):  # executes once; does not participate in scheduling
                tag = f"{scheduler_name}:{action_name}"
                action = self.get_action(action_name)
                try:
                    action.execute(tag=tag)
                    logger.info(f"Execution: tag ({tag}); executed action ({action})")
                except Exception as exception:
                    logger.exception(
                        f"Execution: tag ({tag}); error while executing action ({action})",
                        exc_info=exception,
                    )
                return
            action_names = self.scheduled_actions.actions(scheduler_name)
            if action_name in action_names:
                return  # don't need to schedule
            else:
                self.scheduled_actions.add(scheduler_name, action_name)
                action_names = self.scheduled_actions.actions(scheduler_name)
                if len(action_names) == 1:  # > 1 implies already scheduled
                    scheduler.schedule(
                        scheduler_name,
                        Executor(
                            self.get_actions_for_scheduler,
                            self.unschedule_scheduler_thunk,
                        ),
                    )
            self.save_current()

    def unschedule_scheduler_action(self, scheduler_name: str, action_name: str):
        with Lok.lock:
            self.check_scheduler_name(scheduler_name)
            self.check_action_name(action_name)
            # get the scheduler
            scheduler = self.get_scheduler(scheduler_name)
            if isinstance(scheduler, TimedScheduler):
                scheduler.set_timed(self._timed)
            # remove the action from the scheduler's actions
            scheduler_name = self.scheduled_actions.delete(scheduler_name, action_name)
            # unschedule the scheduler if a non-None scheduler name is returned
            if scheduler_name:
                scheduler.unschedule(scheduler_name)
            self.save_current()

    def unschedule_scheduler(self, scheduler_name: str):
        with Lok.lock:
            self.check_scheduler_name(scheduler_name)
            scheduler = self.get_scheduler(scheduler_name)
            if isinstance(scheduler, TimedScheduler):
                scheduler.set_timed(self._timed)
            scheduler.unschedule(scheduler_name)
            self.scheduled_actions.delete_scheduler(scheduler_name)
            self.save_current()

    def reschedule_scheduler(self, scheduler_name: str):
        with Lok.lock:
            self.check_scheduler_name(scheduler_name)
            scheduler = self.get_scheduler(scheduler_name)
            if isinstance(scheduler, TimedScheduler):
                scheduler.set_timed(self._timed)
            scheduler.schedule(
                scheduler_name,
                Executor(
                    self.get_actions_for_scheduler, self.unschedule_scheduler_thunk
                ),
            )

    def reschedule_all_schedulers(self):
        with Lok.lock:
            for scheduler_name in self.scheduled_actions.scheduler_names():
                self.reschedule_scheduler(scheduler_name)

    def get_scheduled_action_count(self):
        # returns the total number of actions in the scheduled_actions dictionary
        # should be equal to the number of jobs in related Timed instance
        with Lok.lock:
            return self.scheduled_actions.action_count()

    # defer scheduler/action
    def defer_action(self, scheduler_name: str, action_name: str, wait_until: datetime):
        """
        This method defers the start of scheduling an action. The data structure is a dictionary
        with a datetime as the key and a scheduled_actions style dictionary as the value.
        """
        with Lok.lock:
            self.check_scheduler_name(scheduler_name)
            self.check_action_name(action_name)
            self.deferred_scheduled_actions.apply_date(
                scheduler_name=scheduler_name,
                action_name=action_name,
                date_time=wait_until,
            )
            self.save_current()

    def check_for_deferred_actions(self):
        """
        This gets run as a job in the out-of-band Timed instance.

        It looks for deferred actions whose dates are prior to the current
        time and schedules them using the associated scheduler. See the
        defer_action and initialize methods for more details.
        """
        with Lok.lock:
            self.deferred_scheduled_actions.check_for_dated_actions(
                schedule_update_thunk=self.schedule_action,
                verb="schedule",
            )
            self.save_current()

    def get_deferred_action_count(self):
        # returns the total number of actions in the deferred actions dictionary (a dictionary
        # of dictionaries)
        with Lok.lock:
            return self.deferred_scheduled_actions.action_count()

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
            self.check_scheduler_name(scheduler_name)
            self.check_action_name(action_name)
            self.expiring_scheduled_actions.apply_date(
                scheduler_name=scheduler_name,
                action_name=action_name,
                date_time=expire_on,
            )

            self.save_current()

    def check_for_expiring_actions(self):
        """
        This gets run as a job in the out-of-band Timed instance.

        It looks for expiring actions whose dates are later than the current
        time and unschedules them within the context of the associated scheduler.
        See the expire_action and initialize methods for more details.
        """
        with Lok.lock:
            self.expiring_scheduled_actions.check_for_dated_actions(
                schedule_update_thunk=self.unschedule_scheduler_action,
                verb="unschedule",
            )
            self.save_current()

    def get_expiring_action_count(self):
        # returns the total number of actions in the deferred actions dictionary (a dictionary
        # of dictionaries)
        with Lok.lock:
            return self.expiring_scheduled_actions.action_count()

    def clear_all_expiring_actions(self):
        with Lok.lock:
            self.expiring_scheduled_actions.clear()
            self.save_current()

    # utility
    def check_scheduler_name(self, scheduler_name: str, invert: bool = False):
        if invert:
            assert (
                scheduler_name not in self.schedulers
            ), f"scheduler ({scheduler_name}) already exists"
        else:
            assert (
                scheduler_name in self.schedulers
            ), f"scheduler ({scheduler_name}) does not exist"

    def check_action_name(self, action_name: str, invert: bool = False):
        if invert:
            assert (
                action_name not in self.actions
            ), f"action ({action_name}) already exists"
        else:
            assert action_name in self.actions, f"action ({action_name}) does not exist"

    def check_program_name(self, program_name: str, invert: bool = False):
        if invert:
            assert (
                program_name not in self.programs
            ), f"program ({program_name}) already exists"
        else:
            assert (
                program_name in self.programs
            ), f"program ({program_name}) does not exist"

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
            deferred_programs = dictionary["deferred_programs"]
            # deferred_scheduled_programs = dictionary["deferred_scheduled_programs"]
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
                expiring_scheduled_actions=expiring_scheduled_actions,
                deferred_programs=deferred_programs,
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
