import requests
import logging
from typing import Optional
from whendo.core.action import Action, Rez


logger = logging.getLogger(__name__)


class SendPayload(Action):
    """
    This class sends a payload dictionary to a url.
    """

    url: Optional[str] = None
    payload: Optional[dict] = None

    def description(self):
        return f"This action sends payload ({self.payload()}) to ({self.url})."

    def execute(self, tag: str = None, rez: Rez = None):
        flds = self.compute_flds(rez=rez)
        url = flds["url"]
        if url == None:
            raise ValueError("url missing")
        payload = flds["payload"]
        if payload == None:
            raise ValueError("payload missing")
        response = requests.post(url, payload)
        if response.status_code != requests.codes.ok:
            raise Exception(response)
        result = f"payload (payload sent to url ({url})."
        return self.action_result(result=result, rez=rez, flds=rez.flds if rez else {})
