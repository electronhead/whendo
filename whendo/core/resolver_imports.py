"""
That these modules are imported here ensures that Action and Scheduler resolution will use their entire
inheritance trees to resolve an instance from a dictionary. See ./resolver.py.
"""
import whendo.core.actions.file_action
import whendo.core.actions.http_action
import whendo.core.actions.logic_action
import whendo.core.actions.sys_action
import whendo.core.schedulers.cont_scheduler
