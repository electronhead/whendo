from typing import Optional
import os
import logging
from typing import Optional
from whendo.core.util import PP, Dirs
from whendo.core.action import Action, Rez

logger = logging.getLogger(__name__)


class FileAppend(Action):
    """
    This action appends supplied stuff to a file.
    """

    file_append: str = "file_append"
    file: Optional[str] = None
    payload: Optional[dict] = None
    relative_to_output_dir: bool = True

    def description(self):
        return f"This action appends payload ({self.payload}) to file ({self.file})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        file = flds["file"]
        if file == None:
            raise ValueError("file missing")
        relative_to_output_dir = flds["relative_to_output_dir"]
        payload = (
            rez.result
            if rez and rez.result is not None
            else (
                flds["payload"]
                if "payload" in flds
                else {"payload": "***PAYLOAD EMPTY***"}
            )
        )
        file = os.path.join(Dirs.output_dir(), file) if relative_to_output_dir else file
        with open(file, "a") as outfile:
            PP.pprint(payload, stream=outfile)
            outfile.write("\n")
        result = f"file ({file}) appended."
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})
