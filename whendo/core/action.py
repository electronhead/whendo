from pydantic import BaseModel
from typing import Dict, Any
from whendo.core.util import PP, IP, Now, object_info

class Action(BaseModel):
    """
    Actions get something done.
    """
    def execute(self, tag:str=None, scheduler_info:dict=None):
        """
        This method attempts to do something useful and return something useful
        """
        return {'result':'something useful happened'}

    def info(self):
        return object_info(self)
    
    def flat(self):
        return self.json()

# auxilliary
   
class ActionPayload:
    """
    This class produces a status-oriented payload, including action and scheduler info.
    """
    @classmethod
    def build(cls, action_info:Dict[str, Any], scheduler_info:Dict[str, Any]=None):
        payload = {}
        payload.update({'action_info':action_info})
        if scheduler_info:
            payload.update({'scheduler_info':scheduler_info})
        payload.update(cls.action_host())
        payload.update(cls.action_time())
        return payload
    @classmethod
    def action_host(cls):
        return {'action_host': IP.addr}
    @classmethod
    def action_time(cls):
        return {'action_time':Now.s()}