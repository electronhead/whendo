from fastapi import APIRouter, status, Depends
from whendo.api.shared import return_success, raised_exception, get_dispatcher
from whendo.core.resolver import resolve_action

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.get("/{action_name}", status_code=status.HTTP_200_OK)
def get_action(action_name: str):
    try:
        return get_dispatcher(router).get_action(action_name=action_name)
    except Exception as e:
        raise raised_exception(f"failed to retrieve the action ({action_name})", e)


@router.post("/{action_name}", status_code=status.HTTP_200_OK)
def add_action(action_name: str, action=Depends(resolve_action)):
    try:
        assert action, f"couldn't resolve class for action ({action_name})"
        get_dispatcher(router).add_action(action_name=action_name, action=action)
        return return_success(f"action ({action_name}) was successfully added")
    except Exception as e:
        raise raised_exception(f"failed to add action ({action_name})", e)


@router.put("/{action_name}", status_code=status.HTTP_200_OK)
def set_action(action_name: str, action=Depends(resolve_action)):
    try:
        assert action, f"couldn't resolve class for action ({action_name})"
        get_dispatcher(router).set_action(action_name=action_name, action=action)
        return return_success(f"action ({action_name}) was successfully updated")
    except Exception as e:
        raise raised_exception(f"failed to update action ({action_name})", e)


@router.delete("/{action_name}", status_code=status.HTTP_200_OK)
def delete_action(action_name: str):
    try:
        get_dispatcher(router).delete_action(action_name=action_name)
        return return_success(f"action ({action_name}) was successfully deleted")
    except Exception as e:
        raise raised_exception(f"failed to delete action ({action_name})", e)


@router.get("/{action_name}/describe", status_code=status.HTTP_200_OK)
def describe_action(action_name: str):
    try:
        return get_dispatcher(router).describe_action(action_name=action_name)
    except Exception as e:
        raise raised_exception(f"failed to describe action ({action_name})", e)


@router.get("/{action_name}/execute", status_code=status.HTTP_200_OK)
def execute_action(action_name: str):
    """
    Two potential types of exceptions below. One resulting from the actual execute_action call and
    the other returned from the execution of the action itself.
    """
    exception = None  # the action's exception if the action generated an exception
    try:
        result = get_dispatcher(router).execute_action(action_name=action_name)
        if not isinstance(result, Exception):
            return result
        else:
            exception = raised_exception(
                f"failed to execute action ({action_name})", result
            )
    except Exception as e:  # from execute_action
        raise raised_exception(f"failed to execute action ({action_name})", e)
    if exception is not None:  # from the action
        raise exception


@router.post("/{action_name}/execute", status_code=status.HTTP_200_OK)
def execute_action_with_data(action_name: str, data: dict):
    """
    Two potential types of exceptions below. One resulting from the actual execute_action call and
    the other returned from the execution of the action itself.
    """
    exception = None  # the action's exception if the action generated an exception
    try:
        result = get_dispatcher(router).execute_action_with_data(
            action_name=action_name, data=data
        )
        if not isinstance(result, Exception):
            return result
        else:
            exception = raised_exception(
                f"failed to execute action ({action_name}) with data ({data})", result
            )
    except Exception as e:  # from execute_action
        raise raised_exception(
            f"failed to execute action ({action_name}) with data ({data})", e
        )
    if exception is not None:  # from the action
        raise exception


@router.put("/execute", status_code=status.HTTP_200_OK)
def execute_supplied_action(action_name: str, action=Depends(resolve_action)):
    try:
        assert action, f"couldn't resolve class for action ({action})"
        return get_dispatcher(router).execute_supplied_action(supplied_action=action)
    except Exception as e:
        raise raised_exception(f"failed to directly execute the action ({action})", e)
