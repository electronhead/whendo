from typing import Dict, Any, Optional
import os
import logging
from whendo.core.util import PP, Dirs, Now, SystemInfo
from whendo.core.action import Action

logger = logging.getLogger(__name__)


class FileHeartbeat(Action):
    """
    This class is primarily for testing and heartbeat purposes.
    """

    file: str
    relative_to_output_dir: bool = True
    xtra: Optional[Dict[str, Any]] = None

    def description(self):
        return f"This action appends various status information to ({self.file})."

    def execute(self, tag: str = None, scheduler_info: Dict[str, Any] = None):
        payload = self.build_payload(self.info(), scheduler_info)
        payload["tag"] = tag if tag else "N/A"
        if self.xtra:
            payload[
                "xtra"
            ] = (
                self.xtra
            )  # dictionaries are sorted by key. Nice to have extra information at the bottom.
        file = (
            os.path.join(Dirs.output_dir(), self.file)
            if self.relative_to_output_dir
            else self.file
        )
        with open(file, "a") as outfile:
            PP.pprint(payload, stream=outfile)
            outfile.write("\n")
        return {"outcome": "file appended", "action": self.info()}

    def set_xtra(self, xtra: Dict[str, Any] = None):
        self.xtra = xtra
        return self

    def get_xtra(self):
        return self.xtra

    def build_payload(
        self, action_info: Dict[str, Any], scheduler_info: Dict[str, Any] = None
    ):
        payload = {}
        payload.update({"action_info": action_info})
        if scheduler_info:
            payload.update({"scheduler_info": scheduler_info})
        payload.update(self.action_host())
        payload.update(self.action_time())
        return payload

    def action_host(self):
        return {"action_host": SystemInfo.get()["host"]}

    def action_time(self):
        return {"action_time": Now.s()}
