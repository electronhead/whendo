"""
An Executor instance executes actions based on schedule names pushed
onto the queue. If a scheduler name lands on the queue, its actions
corresponding to the schedule in the schedule_actions dispatcher
dictionary are executed.

In this manner, action execution is decoupled from the underlying event
mechanism. For example, the Continuous class (from the schedule library)
only sees thunks whose only effect is to push schedule names onto the
executor queue.

When it comes time to handle non-time-specific events, it will just be a
matter of pushing scheduler names to the executor's queue and relying
on the executor to execute the corresponding actions.
"""

from typing import List, Dict
from pydantic import BaseModel, PrivateAttr
from collections import deque
from threading import RLock, Thread, Event
import time
from collections.abc import Callable


class Executor(BaseModel):
    queue: deque = deque()

    # list funny business -- can't assign Callable to variable typed as Callable
    # thinks it's trying to assign into a method
    # so couldn't use setters on these puppies -- setting directly in calling code
    _scheduled_actions_thunk: Callable = PrivateAttr()
    _actions_thunk: Callable = PrivateAttr()
    _cease_run: Event = PrivateAttr()

    def clear(self):
        self.queue.clear()

    def push(self, scheduler_name: str):
        """
        The event triggering mechanism calls this method.
        """
        with Lok.lock:
            self.queue.append(scheduler_name)

    def compute_actions(self, scheduler_name: str):
        """
        Just-in-time computation of actions.
        """
        action_names = self._scheduled_actions_thunk()[scheduler_name]
        actions = self._actions_thunk()
        return zip(action_names, [actions[action_name] for action_name in action_names])

    def run(self):
        self._cease_run = Event()

        class ExecutorThread(Thread):
            @classmethod
            def run(cls):
                while not self._cease_run.is_set():
                    with Lok.lock:
                        while len(self.queue) > 0:
                            scheduler_name = self.queue.popleft()
                            for (action_name, action) in self.compute_actions(scheduler_name):
                                action.execute(tag=f"{scheduler_name}:{action_name}")

        executor_thread = ExecutorThread()
        executor_thread.setDaemon(True)
        executor_thread.start()

    def stop(self):
        self._cease_run.set()


class Lok:
    lock = RLock()

    @classmethod
    def reset(cls):
        cls.lock = RLock()
