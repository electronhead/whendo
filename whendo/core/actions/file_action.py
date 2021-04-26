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
        file = (
            os.path.join(Dirs.output_dir(), flds["file"])
            if self.relative_to_output_dir
            else self.file
        )
        with open(file, "a") as outfile:
            PP.pprint(flds["payload"], stream=outfile)
            outfile.write("\n")
        result = f"file ({flds['file']}) appended."
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})
