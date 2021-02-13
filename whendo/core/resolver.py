"""
These functions resolve mothership element instances from supplied dictionaries.
"""
import whendo.core.action as action
import whendo.core.scheduler as scheduler
import whendo.core.util as util

def resolve_action(dictionary:dict):
    return util.resolve_instance(action.Action, dictionary)

def resolve_scheduler(dictionary:dict):
    return util.resolve_instance(scheduler.Scheduler, dictionary)

def resolve_file_pathe(dictionary:dict):
    return util.FilePathe(**dictionary)
