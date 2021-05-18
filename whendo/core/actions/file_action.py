from typing import Optional, Any
import os
import logging
from typing import Optional
from whendo.core.util import PP, Dirs, Now
from whendo.core.action import Action, Rez

logger = logging.getLogger(__name__)


class FileAppend(Action):
    """
    This action appends supplied stuff to a file.
    """

    file_append: str = "file_append"
    file: Optional[str] = None
    relative_to_output_dir: Optional[bool] = None
    payload: Optional[Any] = None
    header: Optional[str] = None
    print_header: Optional[bool] = None

    def description(self):
        return f"This action appends payload ({self.payload}) to file ({self.file})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        file = flds.get("file", None)
        if file == None:
            raise ValueError("file missing")
        print_header = flds.get("print_header", None)
        if print_header == None:
            print_header = True
        relative_to_output_dir = flds.get("relative_to_output_dir", None)
        if relative_to_output_dir == None:
            relative_to_output_dir = True
        payload = (
            rez.result
            if rez and rez.result is not None
            else flds.get("payload", {"payload": "***PAYLOAD EMPTY***"})
        )
        file = os.path.join(Dirs.output_dir(), file) if relative_to_output_dir else file
        if print_header:
            header_txt = flds.get("header", f"file ({file}) at ({Now.s()})")
            boundary = "".join(["-"] * len(header_txt))
            output_header_txt = f"{boundary}\n{header_txt}\n{boundary}\n"
        with open(file, "a") as outfile:
            if print_header:
                outfile.write(output_header_txt)
            PP.pprint(payload, stream=outfile)
            outfile.write("\n")
        result = f"file ({file}) appended."
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})
