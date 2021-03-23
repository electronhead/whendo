from typing import Dict, Any, Optional
import os
import logging
from typing import Optional
from whendo.core.util import PP, Dirs, Now, SystemInfo
from whendo.core.action import Action

logger = logging.getLogger(__name__)


class FileAppend(Action):
    """
    This action appends supplied stuff to a file. The mode field
    determines what to do with the field, payload, and the argument,
    data.

    P -- use payload (P). if absent use data (D).
    D -- use D. if absent use P.
    PD -- use P containing D if both. P if just P. D if just D.
    DP -- use D containing P if both. D if just D. P if just P.

    Note: any mix of lower and upper case are valid modes.

    Usage: two ways
        1. FileAppend using <mode> field
        2. one of FileAppendP, FileAppendD, FileAppendPD, FileAppendDP
    """

    file_append: str = "file_append"
    file: str
    payload: Optional[dict]
    relative_to_output_dir: bool = True
    mode: str = "PD"

    def description(self):
        return f"This action appends <payload> and/or <data> to ({self.file})."

    def execute(self, tag: str = None, data: dict = None):
        payload = self.compute_payload(self.mode, payload=self.payload, data=data)
        file = (
            os.path.join(Dirs.output_dir(), self.file)
            if self.relative_to_output_dir
            else self.file
        )
        with open(file, "a") as outfile:
            PP.pprint(payload, stream=outfile)
            outfile.write("\n")
        result = {"result": payload, "action_info": self.info()}
        return result

    def compute_payload(
        self, mode: str, payload: Optional[dict] = None, data: dict = None
    ):
        result = {"missing": {"args": "payload,data"}}
        upper_mode = mode.upper()
        if upper_mode == "P":
            if payload:
                result = payload
            elif data:
                result = data
        elif upper_mode == "D":
            if data:
                result = data
            elif payload:
                result = payload
        elif upper_mode == "DP":
            if data:
                result = data
                if payload:
                    result["payload"] = payload
            elif payload:
                result = payload
        elif upper_mode == "PD":
            if payload:
                result = payload
                if data:
                    result["data"] = data
            elif data:
                result = data
        else:
            raise ValueError(
                f"invalid file append mode ({self.mode}); should be one of 'P', 'D', 'PD', 'DP"
            )
        return result


class FileAppendP(FileAppend):
    """ one of the two, with payload having precedence"""

    file_append_p: str = "file_append_p"
    mode = "P"

    def description(self):
        return f"This action appends payload, otherwise data to ({self.file})."


class FileAppendD(FileAppend):
    """ one of the two, with data having precedence"""

    file_append_d: str = "file_append_d"
    mode = "D"

    def description(self):
        return f"This action appends data, otherwise payload to ({self.file})."


class FileAppendPD(FileAppend):
    """ one or both, with data inside payload """

    file_append_pd: str = "file_append_pd"
    mode = "PD"

    def description(self):
        return f"This action appends data inside payload to ({self.file})."


class FileAppendDP(FileAppend):
    """ one or both, with payload inside data """

    file_append_dp: str = "file_append_dp"
    mode = "DP"

    def description(self):
        return f"This action appends payload inside data to ({self.file})."
