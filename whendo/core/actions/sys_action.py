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

    def execute(self, tag: str = None, data: dict = None):
        result = {"result": util.SystemInfo.get()}
        if data:
            result["data"] = data
        return result


class MiniInfo(Action):
    """
    Return terse local info.
    """

    mini_info = "mini_info"

    def description(self):
        return f"This action returns terse local information."

    def execute(self, tag: str = None, data: dict = None):
        result = {"result": self.local_info()}
        if data:
            result["data"] = data
        return result


class Pause(Action):
    """
    Sleep for supplied int seconds. It's best to make sure that the sleep duration
    does not interfere with job execution (blocking the thread).
    """

    pause: str = "pause"
    seconds: float = 1.0

    def description(self):
        return f"This action sleeps for {self.seconds} second{'s' if self.seconds != 1 else ''}."

    def execute(self, tag: str = None, data: dict = None):
        time.sleep(self.seconds)
        result = {"result": self.seconds, "action_info": self.info()}
        if data:
            result["data"] = data
        return result
