from fastapi import APIRouter, status, Depends
from whendo.api.shared import return_success, raised_exception, get_dispatcher
from whendo.core.resolver import resolve_action

router = APIRouter(prefix="/execution", tags=["Execution"])

# uses put because you cannot supply an Action using get; the use case is RPC - not supported by protocol, hence the hack
@router.put("", status_code=status.HTTP_200_OK)
def execute_supplied_action(action=Depends(resolve_action)):
    try:
        assert action, f"couldn't resolve class for action ({action})"
        return get_dispatcher(router).execute_supplied_action(supplied_action=action)
    except Exception as e:
        raise raised_exception(f"failed to directly execute the action ({action})", e)
