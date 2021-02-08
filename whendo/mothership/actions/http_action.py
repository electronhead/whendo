from typing import Optional
import requests
from mothership.action import Action, ActionPayload
from mothership.util import PP, IP, Now, object_info, HttpVerb

class SendHeartbeat(Action):
    """
    This class sends status information to a url.
    """
    url: str
    xtra: Optional[dict]=None

    def execute(self, tag=None, scheduler_info:dict=None):
        payload = ActionPayload.build(action_info=self.info(), scheduler_info=scheduler_info)
        payload['tag'] = tag if tag else 'N/A'
        if self.xtra:
            payload['xtra'] = self.xtra # dictionaries are sorted by key. Nice to have extra information at the bottom.
        response = requests.get(self.url, payload)
        if response.status_code != requests.codes.ok:
            raise Exception(response)
        return response.json()