from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from .util import object_info, SystemInfo, Rez


logger = logging.getLogger(__name__)


class Action(BaseModel):
    """
    Actions get something done.
    """

    def description(self):
        return "This has no description."

    def execute(self, tag: str = None, rez: Rez = None) -> Rez:
        return self.action_result(rez=rez)

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

    def fields(self):
        """
        Return only non-meta fields.
        """
        return set(
            name for name in self.__fields__ if self.__fields__[name].default != name
        )

    def field_values(self):
        return {
            f: self.__dict__[f] for f in self.fields() if self.__dict__[f] is not None
        }

    def compute_flds(self, rez: Rez = None):
        field_values = self.field_values()
        if rez and rez.flds:
            # selected_flds = {
            #     key: rez.flds[key] for key in self.fields() if key not in field_values
            # }
            # return {**field_values, **selected_flds}
            rez_flds = rez.flds.copy()
            rez_flds.update(field_values)
            return rez_flds
        else:
            return field_values

    def complete_fields(self, rez: Rez):
        """
        This method sets None-fields to the values
        in rez.flds (if extant). Needed for situations
        when an action and rez need to be passed to
        the api using http from within the dispatcher.

        For some reason ActionRez resolution is not
        handled properly within FastAPI's handling
        of /execute/with_rez requests. resolve_action_rez
        works fine independently of FastAPI. This hack
        will remain indefinitely. Its use means that
        the Rez instance will not be propagated in
        downstream execution method calls.
        """
        if rez and rez.flds:
            rez_flds = rez.flds
            self_fields = self.field_values()
            for name in self.fields():
                if name not in self_fields and name in rez_flds:
                    self.__setattr__(name, rez_flds[name])

    def action_result(
        self,
        result: Any = None,
        flds: Optional[Dict[str, Any]] = {},
        rez: Optional[BaseModel] = None,
        extra: Optional[Dict[str, Any]] = None,
        info: Optional[Dict[str, Any]] = None,
    ):
        return Rez(
            result=result,
            flds=flds,
            rez=rez,
            extra=extra,
            info=info if info else self.info(),
        )


class ActionRez(Action):
    action: Action
    rez: Rez


class RezDict(Action):
    rez: Rez
    dictionary: dict
