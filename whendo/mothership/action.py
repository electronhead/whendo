from pydantic import BaseModel

from mothership.util import PP, IP, Now, object_info

class Action(BaseModel):
    """
    Actions get something done.
    """
    def execute(self, tag=None, scheduler_info:dict=None):
        """
        This method does something and returns a useful result. If
        the action's benefit is only a side-effect, then returning some status information
        would be the polite thing to do.
        """
        pass

    def info(self):
        return object_info(self)

# auxilliary
   
class ActionPayload:
    """
    This class produces a status-oriented payload, including action and scheduler info.
    """
    @classmethod
    def build(cls, action_info:dict, scheduler_info:dict):
        payload = {}
        payload.update({'action_info':action_info})
        if scheduler_info:
            payload.update({'scheduler_info':scheduler_info})
        payload.update(cls.action_ip_address())
        payload.update(cls.action_time())
        return payload
    @classmethod
    def action_ip_address(cls):
        return {'action_ip_address': IP.addr}
    @classmethod
    def action_time(cls):
        return {'action_time':Now.s()}