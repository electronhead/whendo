"""
This class implements a single process-based system for defining and scheduling actions local
to the python runtime (api server, testing harness). The class implements all of the potential
endpoints of a restful api and supports testing outside of the restful api implementation.

Instances of this class contain Schedulers and Actions, which can at any point be submitted to and removed from the
job scheduling mechanism of the schedule library (refer to the 'continuous' module).
"""
from pydantic import BaseModel, PrivateAttr
from threading import RLock
import pickle
import json
import os
from whendo.core.util import PP, Dirs
from whendo.core.action import Action
from whendo.core.scheduler import Scheduler
from whendo.core.continuous import Continuous
from whendo.core.resolver import resolve_action, resolve_scheduler

class Mothership(BaseModel):
    """
    Serializations of this class are stored in the local file system. When a runtime starts
    up, Mothership loads the last saved version.
    """
    actions: dict={}
    schedulers: dict={}
    schedulers_actions: dict={}
    saved_dir: str=None

    # not treated as a model attr
    _continuous: Continuous = PrivateAttr(default_factory = Continuous.get)

    def get_continuous(self):
        return self._continuous
    def set_continuous(self, continuous:Continuous):
        self._continuous = continuous

    def get_actions(self):
        with Lok.lock:
            return self.actions
    def get_schedulers(self):
        with Lok.lock:
            return self.schedulers
    def get_schedulers_actions(self):
        with Lok.lock:
            return self.schedulers_actions

    def initialize(self):
        Lok.reset()
    def pprint(self):
        PP.pprint(self.dict())
    
    def load_current(self):
        return self.load_from_name('current')
    def save_current(self):
        with Lok.lock:
            self.save_to_name('current')

    def load_from_name(self, name:str):
        with Lok.lock:
            assert self.saved_dir, 'saved_dir must be set'
            with open(self.saved_dir+name+'.json', 'r') as infile:
                json_string = json.load(infile)
                dictionary = json.loads(json_string)
                return Mothership.resolve(dictionary)
    def save_to_name(self, name:str):
        with Lok.lock:
            assert self.saved_dir, 'saved_dir must be set'
            with open(self.saved_dir+name+'.json', 'w') as outfile:
                json.dump(self.json(), outfile, indent=2)

    def get_saved_dir(self):
        return self.saved_dir
    def set_saved_dir(self, saved_dir:str):
        with Lok.lock:
            if not os.path.exists(saved_dir):
                os.makedirs(saved_dir)
            self.saved_dir = saved_dir
            self.save_current()

    def clear_all(self):
        with Lok.lock:
            schedulers_copy = self.schedulers.copy()
            for scheduler_name in schedulers_copy:
                self.remove_scheduler(scheduler_name)
            actions_copy = self.actions.copy()
            for action_name in actions_copy:
                self.remove_action(action_name)
            self.schedulers_actions.clear()
            self.save_current()

    def get_scheduled_action_count(self):
        # returns the total number of actions in the schedulers_actions dictionary
        # should be equal to the number of jobs in related Continuous instance
        with Lok.lock:
            return sum(len(action_array) for action_array in self.schedulers_actions.values())

    def add_action(self, action_name:str, action:Action):
        with Lok.lock:
            assert not action_name in self.actions, f"action ({action_name}) already exists"
            self.actions[action_name] = action
            self.save_current()
    def get_action(self, action_name:str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            return self.actions.get(action_name)
    def remove_action(self, action_name:str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            for scheduler_name in self.schedulers:
                self.unschedule_action(action_name)
                action_names = self.schedulers_actions[scheduler_name]
                if action_name in action_names: action_names.remove(action_name)
            self.actions.pop(action_name, None)
            self.save_current()
    def update_action(self, action_name:str, dictionary:dict):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            action = self.actions.get(action_name)
            action.__dict__.update(dictionary)
            self.reschedule_action(action_name)
            self.save_current()
    def execute_action(self, action_name:str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            return self.get_action(action_name).execute()

    # schedulers
    def add_scheduler(self, scheduler_name:str, scheduler:Scheduler):
        with Lok.lock:
            assert not scheduler_name in self.schedulers, f"scheduler ({scheduler_name}) already exists"
            self.schedulers[scheduler_name] = scheduler
            self.schedulers_actions[scheduler_name] = []
            self.save_current()
    def get_scheduler(self, scheduler_name:str):
        with Lok.lock:
            return self.schedulers.get(scheduler_name, None)
    def remove_scheduler(self, scheduler_name:str):
        with Lok.lock:
            assert scheduler_name in self.schedulers, f"scheduler ({scheduler_name}) does not exist"
            self.unschedule_scheduler(scheduler_name)
            self.schedulers.pop(scheduler_name)
            self.schedulers_actions[scheduler_name].clear() # pro-actively clean up. less work for GC.
            self.schedulers_actions.pop(scheduler_name)
            self.save_current()
    def update_scheduler(self, scheduler_name:str, dictionary:dict):
        with Lok.lock:
            assert scheduler_name in self.schedulers, f"scheduler ({scheduler_name}) does not exist"
            scheduler = self.schedulers.get(scheduler_name)
            scheduler.__dict__.update(dictionary)
            self.reschedule_scheduler(scheduler_name)
            self.save_current()
    def execute_scheduler_actions(self, scheduler_name:str):
        with Lok.lock:
            assert scheduler_name in self.schedulers, f"scheduler ({scheduler_name}) does not exist"
            result = []
            for action_name in self.schedulers_actions.get(scheduler_name, []):
                result.append(self.get_action(action_name).execute())
            return result

    # scheduling
    def schedule_action(self, scheduler_name:str, action_name:str):
        with Lok.lock:
            assert scheduler_name in self.schedulers, f"scheduler ({scheduler_name}) does not exist"
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            assert not action_name in self.schedulers_actions[scheduler_name]
            scheduler = self.get_scheduler(scheduler_name)
            action = self.actions.get(action_name)
            tag = self.scheduler_tag(scheduler_name, action_name)
            scheduler.schedule_action(tag, action, self._continuous)
            self.schedulers_actions[scheduler_name].append(action_name)
            self.save_current()
    def unschedule_action(self, action_name:str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            for scheduler_name in self.schedulers_actions:
                if action_name in self.schedulers_actions[scheduler_name]:
                    tag = self.scheduler_tag(scheduler_name, action_name)
                    self._continuous.clear(tag)
                    action_names = self.schedulers_actions[scheduler_name]
                    if action_name in action_names: action_names.remove(action_name)
            self.save_current()
    def reschedule_action(self, action_name:str):
        with Lok.lock:
            assert action_name in self.actions, f"action ({action_name}) does not exist"
            for scheduler_name in self.schedulers_actions:
                if action_name in self.schedulers_actions[scheduler_name]:
                    tag = self.scheduler_tag(scheduler_name, action_name)
                    self._continuous.clear(tag)
                    scheduler = self.get_scheduler(scheduler_name)
                    action = self.actions[action_name]
                    scheduler.schedule_action(tag, action, self._continuous)
    def unschedule_scheduler(self, scheduler_name:str):
        with Lok.lock:
            assert scheduler_name in self.schedulers, f"scheduler ({scheduler_name}) does not exist"
            for action_name in self.schedulers_actions[scheduler_name]:
                tag = self.scheduler_tag(scheduler_name, action_name)
                self._continuous.clear(tag)
            self.schedulers_actions[scheduler_name].clear()
            self.save_current()
    def reschedule_scheduler(self, scheduler_name:str):
        with Lok.lock:
            assert scheduler_name in self.schedulers, f"scheduler ({scheduler_name}) does not exist"
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
  
    # utility
    def scheduler_tag(self, schedule_name:str, action_name:str):
        # computes job tag for scheduler and action
        return f"{schedule_name}:{action_name}"
        
    @classmethod
    def resolve(cls, dictionary:dict={}):
        """
        converts dictionary to an Mothership instance.
        """
        if len(dictionary) == 0:
            return Mothership(saved_dir=Dirs.saved_dir)
        else:
            saved_dir = dictionary['saved_dir']
            actions = dictionary['actions']
            schedulers = dictionary['schedulers']
            schedulers_actions = dictionary['schedulers_actions']
            # replace key's value for each key...
            for action_name in actions:
                actions[action_name] = resolve_action(actions[action_name])
            for scheduler_name in schedulers:
                schedulers[scheduler_name] = resolve_scheduler(schedulers[scheduler_name])
            return Mothership(
                saved_dir=saved_dir,
                actions=actions,
                schedulers=schedulers,
                schedulers_actions=schedulers_actions)

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

class MothershipsLittleHelper:
    # this call returns the standard non-test Mothership singleton
    mothership = None
    @classmethod
    def get(cls):
        if not cls.mothership:
            cls.mothership = Mothership(saved_dir=Dirs.saved_dir())
            try:    
                cls.mothership = cls.mothership.load_current()
            except Exception as e:
                print(e) # TODO: log it!
            cls.mothership.set_continuous(Continuous.get())
            cls.mothership.initialize()
            cls.mothership.reschedule_all_schedulers()
        return cls.mothership