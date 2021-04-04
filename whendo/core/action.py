from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from collections import namedtuple
from .util import object_info, SystemInfo, Now


logger = logging.getLogger(__name__)


class Action(BaseModel):
    """
    Actions get something done.
    """

    def description(self):
        return "This has no description."

    def execute(self, tag: str = None, data: dict = None):
        """
        This method typically attempts to do something useful and return something useful
        """
        return {"result": "not sure what happened"}

    def info(self):
        return object_info(self)

    def flat(self):
        return self.json()

    def local_host(self):
        return SystemInfo.get()["host"]

    def local_port(self):
        return SystemInfo.get()["port"]

    def local_time(self):
        return SystemInfo.get()["current"]

    def local_info(self):
        return {
            "host": self.local_host(),
            "port": self.local_port(),
            "time": self.local_time(),
        }

    def action_result(self, result: Any = None, data: dict = None, extra: dict = None):
        output = {}
        if result:
            output["result"] = result
        if data:
            output["data"] = data
        if extra:
            output["extra"] = extra
        return output

    @classmethod
    def get_result(cls, something: Any):
        if isinstance(something, dict):
            if "result" in something:
                return something["result"]
            else:
                return something
        else:
            return {"result": something}
