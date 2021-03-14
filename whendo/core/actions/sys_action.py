import time
import logging
from whendo.core.action import Action
import whendo.core.util as util


logger = logging.getLogger(__name__)


class SysInfo(Action):
    """
    Return system info
    """

    sys_info = "sys_info"

    def description(self):
        return f"This action returns system-level information."

    def execute(self, tag: str = None, scheduler_info: dict = None):
        return util.SystemInfo.get()


class Pause(Action):
    """
    Sleep for supplied int seconds. It's best to make sure that the sleep duration
    does not interfere with job execution (blocking the thread).
    """

    seconds: int = 1

    def description(self):
        return f"This action sleeps for {self.seconds} second{'s' if self.seconds > 1 else ''}."

    def execute(self, tag: str = None, scheduler_info: dict = None):
        return time.sleep(self.seconds)
