from pydantic import BaseModel
from typing import Dict, Any, Optional
from logging import Logger, getLogger
from .util import object_info, SystemInfo, Rez


logger = getLogger(__name__)


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
            rez_flds = rez.flds.copy()
            rez_flds.update(field_values)
            return rez_flds
        else:
            return field_values

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


def log_action_result(
    calling_logger: Logger,
    calling_object: Any,
    action: Action,
    result: Rez,
    tag: str = None,
):
    calling_logger.info(
        f"CLASS ({calling_object.__class__.__name__}) TAG ({tag}) ACTION ({action}) RESULT ({result.flatten_results() if result else None})"
    )


class ActionRez(Action):
    action: Action
    rez: Rez


class RezDict(Action):
    rez: Rez
    dictionary: dict
