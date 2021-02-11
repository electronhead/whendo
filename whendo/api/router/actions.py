
from fastapi import APIRouter, status, Depends
from whendo.api.shared import return_success, raised_exception, get_mothership
from whendo.core.resolver import resolve_action

router = APIRouter(
    prefix='',
    tags=['Actions']
)

@router.get('/actions/{action_name}', status_code=status.HTTP_200_OK)
def get_action(action_name:str):
    try:
        action = get_mothership(router).get_action(action_name=action_name)
        return return_success(action)
    except Exception as e:
        raise raised_exception(f"failed to retrieve the action ({action_name})", e)

@router.put('/actions/{action_name}', status_code=status.HTTP_200_OK)
def add_action(action_name:str, action=Depends(resolve_action)):
    try:
        assert action, f"couldn't resolve class for action ({action_name})"
        get_mothership(router).add_action(action_name=action_name, action=action)
        return return_success(f"action ({action_name}) was successfully added")
    except Exception as e:
        raise raised_exception(f"failed to add action ({action_name})", e)

@router.delete('/actions/{action_name}', status_code=status.HTTP_200_OK)
def remove_action(action_name:str):
    try:
        get_mothership(router).remove_action(action_name=action_name)
        return return_success(f"action ({action_name}) was successfully removed")
    except Exception as e:
        raise raised_exception(f"failed to remove action ({action_name})", e)

@router.patch('/actions/{action_name}', status_code=status.HTTP_200_OK)
def update_action(action_name:str, dictionary:dict):
    try:
        get_mothership(router).update_action(action_name=action_name, dictionary=dictionary)
        return return_success(f"action ({action_name}) was successfully updated")
    except Exception as e:
        raise raised_exception(f"failed to update action ({action_name})", e)

@router.get('/actions/{action_name}/execute', status_code=status.HTTP_200_OK)
def execute_action(action_name:str):
    """
    Two potential types of exceptions below. One resulting from the actual execute_action call and
    the other returned from the execution of the action itself.
    """
    exception = None # the action's exception if the action generated an exception
    try:
        result = get_mothership(router).execute_action(action_name=action_name)
        if not isinstance(result, Exception):
            return return_success({'msg': f"action ({action_name}) was successfully executed", 'result':result})
        else:
            exception = raised_exception(f"failed to execute action ({action_name})", result)
    except Exception as e: # from execute_action
        raise raised_exception(f"failed to execute action ({action_name})", e)
    if exception is not None: # from the action
        raise exception


@router.get('/actions/{action_name}/unschedule', status_code=status.HTTP_200_OK)
def unschedule_action(action_name:str):
    try:
        get_mothership(router).unschedule_action(action_name=action_name)
        return return_success(f"action ({action_name}) was successfully unscheduled")
    except Exception as e:
        raise raised_exception(f"failed to unschedule action ({action_name})", e)