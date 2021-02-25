from whendo.core.action import Action
from whendo.core.util import SystemInfo


class SystemInfoAction(Action):
    """
    Return system info
    """

    system_info = "system_info"

    def execute(self, tag: str = None, scheduler_info: dict = None):
        return SystemInfo.get()
