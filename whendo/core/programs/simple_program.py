from typing import List, Dict
import logging
from datetime import datetime, timedelta
from typing import Optional
from whendo.core.program import Program, ProgramItem


logger = logging.getLogger(__name__)


class PBEProgram(Program):
    """
    A prologue/body/epilogue Program has a prologue, body, and
    epilogue.

    1. prologue action name -- invoked at the start time
    2. epilogue action name -- invoked at the stop time
    3. body -- a schedulers/actions-structured dictionary
        These schedulers/actions are deferred until...
            start datetime + offset seconds
        and expire
            stop datetime - offset seconds

    usage:

        pbe = PBEProgram()
            .body_element("heartbeat", "turn_on_pin_A")
            .body_element("heartbeat2", "report_activity")
            .epilogue("clear_gpio")
            .prologue("start_pivot")
        pbe = PBEProgram(
            prologue_name="start_pivot",
            epilogue_name="clear_gpio",
            body={"heartbeat": ["turn_on_pin_A"],
                "heartbeat2", ["report_activity"]}
            )
    """

    prologue_name: Optional[str] = None
    epilogue_name: Optional[str] = None
    body: Dict[str, List[str]] = {}
    offset_seconds: int = 0

    def description(self):
        return f"This program starts with action ({self.prologue_name}) and ends with ({self.epilogue_name}) with scheduled actions ({self.body}) in between."

    def compute_program_items(self, start: datetime = None, stop: datetime = None):
        """
        Note: None is supplied when ensuring existence of action and scheduler names in the dispatcher.
        """
        result = []
        if self.prologue_name:
            result.append(
                ProgramItem("defer", start, "immediately", self.prologue_name)
            )

        if len(self.body) > 0:
            timedelta_offset = timedelta(seconds=self.offset_seconds)
            start_plus = start + timedelta_offset if start else None
            stop_minus = stop - timedelta_offset if stop else None
            for scheduler_name in self.body:
                for action_name in self.body[scheduler_name]:
                    result.append(
                        ProgramItem("defer", start_plus, scheduler_name, action_name)
                    )
                    result.append(
                        ProgramItem("expire", stop_minus, scheduler_name, action_name)
                    )

        if self.epilogue_name:
            result.append(ProgramItem("defer", stop, "immediately", self.epilogue_name))

        return result

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
