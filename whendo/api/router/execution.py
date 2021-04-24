from fastapi import APIRouter, status, Depends
from whendo.api.shared import return_success, raised_exception, get_dispatcher
from whendo.core.resolver import resolve_action

router = APIRouter(prefix="/execution", tags=["Execution"])

# uses put because you cannot supply an Action using get; the use case is RPC - not supported by protocol, hence the hack
@router.post("", status_code=status.HTTP_200_OK)
def execute_supplied_action(supplied_action=Depends(resolve_action)):
    try:
        assert supplied_action, f"couldn't resolve class for action ({supplied_action})"
        return get_dispatcher(router).execute_supplied_action(
            supplied_action=supplied_action
        )
    except Exception as e:
        raise raised_exception(
            f"failed to directly execute the action ({supplied_action})", e
        )


@router.post("/with_data", status_code=status.HTTP_200_OK)
def execute_supplied_action_with_data(data: dict, supplied_action_as_dict: dict):
    """
    The supplied action needs to be passed as a dict since BaseModel instsances
    can not be resolved inside a dictionary, which is required due to the multiple
    objects being passed through the api.
    """
    try:
        supplied_action = resolve_action(supplied_action_as_dict)
        assert supplied_action, f"couldn't resolve class for action ({supplied_action})"
        return get_dispatcher(router).execute_supplied_action_with_data(
            supplied_action=supplied_action, data=data
        )
    except Exception as e:
        raise raised_exception(
            f"failed to directly execute the action ({supplied_action}) with data ({data})",
            e,
        )
