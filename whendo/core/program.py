from typing import List, Dict
import logging
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class Program(BaseModel):
    """
    A Program encapsulates schedulers and actions into one
    entity, so that it can be executed between a start time and
    stop time. See Dispatcher.scheduler_program for implementation
    details. There may be other types of Programs in the future,
    but the implementation of Program's behavior is implicitly tied to a
    Dispatcher, which also has references to the Program class itself,
    leading to mutual recursion. This may require re-factoring the
    Dispatcher code to eliminate the recursion. In the meantime, the
    current implementation avoids mutual recursion and offers enough
    functionality. When other combinations of Schedulers and Actions
    seem worthwhile, this recursion issue can be revisited at that time.

    1. prologue action name -- invoked at the start time
    2. epilogue action name -- invoked at the stop time
    3. body -- a schedulers/actions-structured dictionary
        These schedulers/actions are deferred until...
            start datetime + offset seconds
        and expire
            stop datetime - offset seconds

    usage:

    profile = Profile()
        .body_element("heartbeat", "turn_on_pin_A")
        .body_element("heartbeat2", "report_activity")
        .epilogue("clear_gpio")
        .prologue("start_pivot")
    profile = Profile(
        prologue="start_pivot",
        epilogue="clear_gpio",
        body={"heartbeat": ["turn_on_pin_A"],
            "heartbeat2", ["report_activity"]}
        )
    """

    prologue_name: str = "NOT_APPLICABLE"
    epilogue_name: str = "NOT_APPLICABLE"
    body: Dict[str, List[str]] = {}
    offset_seconds: int = 0

    def description(self):
        return f"This program starts with action ({self.prologue_name}) and ends with ({self.epilogue_name}) with scheduled actions ({self.body}) in between."

    def body_element(self, scheduler_name: str, action_name: str):
        if scheduler_name not in self.body:
            self.body[scheduler_name] = [action_name]
        elif action_name not in self.body[scheduler_name]:
            self.body[scheduler_name].append(action_name)
        return self

    def prologue(self, prologue_name: str):
        self.prologue_name = prologue_name
        return self

    def epilogue(self, epilogue_name: str):
        self.epilogue_name = epilogue_name
        return self
