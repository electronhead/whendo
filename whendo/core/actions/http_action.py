import requests
from typing import Optional, Dict, Any
from whendo.core.action import Action
from whendo.sdk.client import Client


class SendPayload(Action):
    """
    This class sends a payload dictionary to a url.
    """

    url: str
    payload: Optional[Dict[str, Any]] = None

    def execute(self, tag: str = None, scheduler_info: dict = None):
        response = requests.get(self.url, self.payload)
        if response.status_code != requests.codes.ok:
            raise Exception(response)
        return response.json()


class ExecuteAction(Action):
    """
    Execute an action at host:port.
    """

    host: str
    port: int
    action_name: str

    def execute(self, tag: str = None, scheduler_info: dict = None):
        return Client(host=self.host, port=self.port).execute_action(self.action_name)
