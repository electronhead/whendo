"""
These functions resolve mothership element instances from supplied dictionaries.
"""
import whendo.core.action as action
import whendo.core.scheduler as scheduler
import whendo.core.util as util

def resolve_action(dictionary:dict):
    found_class = util.find_class(action.Action, dictionary)
    try:
        resolved = found_class.resolve(dictionary) # for Action instances with embedded Action instances
    except:
        resolved = util.resolve_instance(action.Action, dictionary) # default handling
    return resolved

def resolve_scheduler(dictionary:dict):
    return util.resolve_instance(scheduler.Scheduler, dictionary)

def resolve_file_pathe(dictionary:dict):
    return util.FilePathe(**dictionary)
