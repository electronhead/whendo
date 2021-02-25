from typing import Dict, Any, Optional
import os
from whendo.core.util import PP, Dirs
from whendo.core.action import Action, ActionPayload


class FileHeartbeat(Action):
    """
    This class appends status information to a file. This information can include
    a dictionary [xtra] supplied at instantiation.
    """

    file: str
    relative_to_output_dir: bool = True
    xtra: Optional[Dict[str, Any]] = None

    def execute(self, tag: str = None, scheduler_info: Dict[str, Any] = None):
        payload = ActionPayload.build(
            action_info=self.info(), scheduler_info=scheduler_info
        )
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
