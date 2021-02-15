"""
These functions resolve dispatcher element instances from supplied dictionaries.
"""
from pydantic import ValidationError
import whendo.core.action as action
import whendo.core.scheduler as scheduler
import whendo.core.util as util

def resolve_action(dictionary:dict, check_for_found_class:bool=True):
    return util.resolve_instance(action.Action, dictionary, check_for_found_class=check_for_found_class)

def resolve_scheduler(dictionary:dict, check_for_found_class:bool=True):
    return util.resolve_instance(scheduler.Scheduler, dictionary, check_for_found_class=check_for_found_class)

def resolve_file_pathe(dictionary:dict, check_for_found_class:bool=True):
    try:
        return util.FilePathe(**dictionary)
    except ValidationError as error:
        if check_for_found_class:
            raise error
        else:
            return dictionary
