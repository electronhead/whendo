"""
These functions resolve dispatcher element instances from supplied dictionaries.
"""
from pydantic import ValidationError
from .action import Action
from .scheduler import Scheduler
from .util import FilePathe, resolve_instance


def resolve_action(dictionary: dict, check_for_found_class: bool = True):
    return resolve_instance(
        Action, dictionary, check_for_found_class=check_for_found_class
    )


def resolve_scheduler(dictionary: dict, check_for_found_class: bool = True):
    return resolve_instance(
        Scheduler, dictionary, check_for_found_class=check_for_found_class
    )


def resolve_file_pathe(dictionary: dict, check_for_found_class: bool = True):
    try:
        return FilePathe(**dictionary)
    except ValidationError as error:
        if check_for_found_class:
            raise error
        else:
            return dictionary
