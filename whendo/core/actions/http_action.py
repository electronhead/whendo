import requests
import logging
import json
from typing import Optional
from whendo.core.action import Action
import whendo.core.util as util_x


logger = logging.getLogger(__name__)


class SendPayload(Action):
    """
    This class sends a payload dictionary to a url.
    """

    url: str
    payload: Optional[dict]

    def description(self):
        return f"This action sends the supplied dictionary payload to ({self.url})."

    def execute(self, tag: str = None, data: dict = None):
        if self.payload:
            payload = self.payload.copy()
            if data:
                payload.update(data)
        elif data:
            payload = data
        else:
            payload = {"result": "no payload"}
        response = requests.post(self.url, payload)
        if response.status_code != requests.codes.ok:
            raise Exception(response)
        result = {"result": response.json(), "action_info": self.info()}
        if data:
            result.update({"data": data})
        return result


class ExecuteAction(Action):
    """
    Execute an action at host:port.
    """

    host: str
    port: int
    action_name: str

    def description(self):
        return f"This action executes ({self.action_name}) at host:port ({self.host}:{self.port}) unless overriden in the supplied dictionary."

    def execute(self, tag: str = None, data: dict = None):
        self.check_host_port(self.host, self.port)
        if data:
            result = {
                "result": util_x.Http(host=self.host, port=self.port).post_dict(
                    f"/actions/{self.action_name}/execute", data
                ),
                "data": data,
            }
        else:
            result = {
                "result": util_x.Http(host=self.host, port=self.port).get(
                    f"/actions/{self.action_name}/execute"
                )
            }
        return result

    def check_host_port(self, host: str, port: int):
        if host == self.local_host() and port == self.local_port():
            raise ValueError(f"host:port must be different from ({host}:{port})")
