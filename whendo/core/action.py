from pydantic import BaseModel
import logging
from .util import object_info


logger = logging.getLogger(__name__)


class Action(BaseModel):
    """
    Actions get something done.
    """

    def description(self):
        return "This Action does nothing."

    def execute(self, tag: str = None, scheduler_info: dict = None):
        """
        This method typically attempts to do something useful and return something useful
        """
        return {"result": "something useful happened"}

    def info(self):
        return object_info(self)

    def flat(self):
        return self.json()
