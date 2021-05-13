"""
These functions resolve dispatcher element instances from supplied dictionaries.
"""
import logging
from pydantic import ValidationError
from .action import Action, ActionRez
from .scheduler import Scheduler
from .program import Program
from .server import Server
from .util import (
    FilePathe,
    resolve_instance,
    resolve_instance_multi_class,
    Rez,
    DateTime,
    DateTime2,
)


logger = logging.getLogger(__name__)


def resolve_action(dictionary: dict, check_for_found_class: bool = True):
    return resolve_instance(
        Action, dictionary, check_for_found_class=check_for_found_class
    )


def resolve_scheduler(dictionary: dict, check_for_found_class: bool = True):
    return resolve_instance(
        Scheduler, dictionary, check_for_found_class=check_for_found_class
    )


def resolve_program(dictionary: dict, check_for_found_class: bool = True):
    return resolve_instance(
        Program, dictionary, check_for_found_class=check_for_found_class
    )


def resolve_server(dictionary: dict, check_for_found_class: bool = True):
    result = resolve_instance(
        Server, dictionary, check_for_found_class=check_for_found_class
    )
    return result


def resolve_rez(dictionary: dict, check_for_found_class: bool = False):
    result = resolve_instance_multi_class(
        [
            Rez,
            DateTime,
            DateTime2,
            Action,
        ],  # BaseModel objects that may be found in a Rez
        dictionary,
        check_for_found_class=check_for_found_class,
    )
    return result


def resolve_action_rez(dictionary: dict, check_for_found_class: bool = False):
    result = resolve_instance_multi_class(
        [
            Rez,
            Action,
            DateTime,
            DateTime2,
            ActionRez,
        ],  # BaseModel objects that may be found in an ActionRez
        dictionary,
        check_for_found_class=check_for_found_class,
    )
    return result


def resolve_file_pathe(dictionary: dict, check_for_found_class: bool = True):
    try:
        return FilePathe(**dictionary)
    except ValidationError as error:
        if check_for_found_class:
            raise error
        else:
            return dictionary
