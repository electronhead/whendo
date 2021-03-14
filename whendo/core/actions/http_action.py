import requests
from typing import Optional, Dict, Any
import logging
from whendo.core.action import Action
from whendo.core.util import Http


logger = logging.getLogger(__name__)


class SendPayload(Action):
    """
    This class sends a payload dictionary to a url.
    """

    url: str
    payload: Optional[Dict[str, Any]] = None

    def description(self):
        return f"This action sends the supplied dictionary payload to ({self.url})."

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

    def description(self):
        return f"This action executes ({self.action_name}) at host ({self.host}) and port ({self.port})."

    def execute(self, tag: str = None, scheduler_info: dict = None):
        return Http(host=self.host, port=self.port).get(
            f"/actions/{self.action_name}/execute"
        )
