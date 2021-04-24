import requests
import logging
import json
from typing import Optional, Dict, Set
from whendo.core.action import Action
import whendo.core.util as util_x
from whendo.core.hooks import DispatcherHooks
from whendo.core.server import Server
from whendo.core.util import KeyTagMode


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
        return self.action_result(result=response.json(), data=data)
