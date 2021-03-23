from typing import Dict, Any, Optional
import os
import logging
from whendo.core.util import PP, Dirs, Now, SystemInfo
from whendo.core.action import Action

logger = logging.getLogger(__name__)


class FileAppend(Action):
    """
    This action appends <data> to a file if <payload> is None.
    """

    file: str
    relative_to_output_dir: bool = True
    payload: Optional[dict]

    def description(self):
        return f"This action appends data to ({self.file})."

    def execute(self, tag: str = None, data: dict = None):
        payload = self.payload if self.payload else data
        if not payload:
            payload = {"result": "no data or payload provided"}
        file = (
            os.path.join(Dirs.output_dir(), self.file)
            if self.relative_to_output_dir
            else self.file
        )
        with open(file, "a") as outfile:
            PP.pprint(data if data else self.payload, stream=outfile)
            outfile.write("\n")
        result = {"result": payload, "action_info": self.info()}


class FileHeartbeat(Action):
    """
    This class is primarily for testing and heartbeat purposes. Appends
    <payload> and, if supplied, <data>.
    """

    file: str
    relative_to_output_dir: bool = True
    payload: Optional[dict]

    def description(self):
        return f"This action appends various status information to ({self.file})."

    def execute(self, tag: str = None, data: dict = None):
        payload = {"action_info": self.info()}
        if data:
            payload["data"] = data
        payload.update(self.local_info())
        file = (
            os.path.join(Dirs.output_dir(), self.file)
            if self.relative_to_output_dir
            else self.file
        )
        with open(file, "a") as outfile:
            PP.pprint(payload, stream=outfile)
            outfile.write("\n")
        return {"result": payload}
