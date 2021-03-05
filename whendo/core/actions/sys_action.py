import time
from whendo.core.action import Action
import whendo.core.util as util


class SysInfo(Action):
    """
    Return system info
    """

    sys_info = "sys_info"

    def execute(self, tag: str = None, scheduler_info: dict = None):
        return util.SystemInfo.get()


class Pause(Action):
    """
    Sleep for supplied int seconds.
    """

    seconds: int = 1

    def execute(self, tag: str = None, scheduler_info: dict = None):
        return time.sleep(self.seconds)
