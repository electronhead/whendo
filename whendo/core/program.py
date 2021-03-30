import logging
from pydantic import BaseModel
from datetime import datetime, timedelta
from collections import namedtuple


logger = logging.getLogger(__name__)

"""
ProgramItems are the link between the dispatcher and programs.

type = defer | expire
dt = datetime.datetime
"""
ProgramItem = namedtuple("ProgramItem", ["type", "dt", "scheduler_name", "action_name"])


class Program(BaseModel):
    """
    A Program encapsulates a set of deferrals and expirations for scheduler/action pairs.
    """

    def compute_program_items(self, start: datetime = None, stop: datetime = None):
        """
        Returns a list of ProgramItems used for scheduling by the dispatcher.
        """
        pass
