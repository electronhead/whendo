from typing import Optional
from whendo.core.util import PP
from whendo.core.action import Action, ActionPayload

class FileHeartbeat(Action):
    """
    This class appends status information to a file. This information can include
    a dictionary [xtra] supplied at instantiation.
    """
    file: str
    xtra: Optional[dict]=None

    def execute(self, tag:str=None, scheduler_info:dict=None):
        payload = ActionPayload.build(action_info=self.info(), scheduler_info=scheduler_info)
        payload['tag'] = tag if tag else 'N/A'
        if self.xtra:
            payload['xtra'] = self.xtra # dictionaries are sorted by key. Nice to have extra information at the bottom.
        with open(self.file, "a") as outfile:
            PP.pprint(payload, stream=outfile)
            outfile.write('\n')
        return {'outcome':'file appended', 'action':self.info()}
    def set_xtra(self, xtra:dict=None):
        self.xtra = xtra
        return self
    def get_xtra(self):
        return self.xtra