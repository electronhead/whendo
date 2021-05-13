from fastapi import APIRouter, status, Depends
from whendo.api.shared import return_success, raised_exception, get_dispatcher
from whendo.core.resolver import resolve_action_rez, resolve_action

router = APIRouter(prefix="/execution", tags=["Execution"])


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


@router.post("/with_rez", status_code=status.HTTP_200_OK)
def execute_supplied_action_with_rez(action_rez=Depends(resolve_action_rez)):
    """
    The supplied action needs to be passed as an ActionRez
    """
    try:
        assert action_rez, f"couldn't resolve class for action_rez ({action_rez})"
        action = action_rez.action
        rez = action_rez.rez
        return get_dispatcher(router).execute_supplied_action_with_rez(
            supplied_action=action, rez=rez
        )
    except Exception as e:
        raise raised_exception(
            f"failed to directly execute the action embedded in ({action_rez})",
            e,
        )
