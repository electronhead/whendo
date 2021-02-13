import requests
from whendo.core.action import Action

class SendPayload(Action):
    """
    This class sends a payload dictionary to a url.
    """
    url:str
    payload:dict

    def execute(self, tag:str=None, scheduler_info:dict=None):
        response = requests.get(self.url, payload)
        if response.status_code != requests.codes.ok:
            raise Exception(response)
        return response.json()