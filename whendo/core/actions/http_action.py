import requests
import logging
import json
from whendo.core.action import Action
from whendo.core.util import Http


logger = logging.getLogger(__name__)


class SendPayload(Action):
    """
    This class sends a payload dictionary to a url.
    """

    url: str
    payload: dict

    def description(self):
        return f"This action sends the supplied dictionary payload to ({self.url})."

    def execute(self, stuf: dict = None):
        payload = self.payload
        if data:
            payload.update({"data": data})
        response = requests.post(self.url, payload)
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

    def execute(self, stuf: dict = None):
        if stuf:
            return Http(host=self.host, port=self.port).post_json(
                f"/actions/{self.action_name}/execute", json.dumps(stuf)
            )
        else:
            return Http(host=self.host, port=self.port).get(
                f"/actions/{self.action_name}/execute"
            )
