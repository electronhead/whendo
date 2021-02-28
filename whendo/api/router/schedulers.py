from fastapi import APIRouter, status, Depends
from typing import Optional
from whendo.api.shared import return_success, raised_exception, get_dispatcher
from whendo.core.resolver import resolve_scheduler
import whendo.core.util as util

router = APIRouter(prefix="", tags=["Schedulers"])


@router.get("/schedulers/action_count", status_code=status.HTTP_200_OK)
def get_scheduled_action_count():
    try:
        return return_success(
            {"action_count": get_dispatcher(router).get_scheduled_action_count()}
        )
    except Exception as e:
        raise raised_exception(f"failed to retrieve the scheduled action count", e)


@router.get("/schedulers/deferred_action_count", status_code=status.HTTP_200_OK)
def get_deferred_action_count():
    try:
        return return_success(
            {
                "deferred_action_count": get_dispatcher(
                    router
                ).get_deferred_action_count()
            }
        )
    except Exception as e:
        raise raised_exception(f"failed to retrieve the deferred action count", e)


@router.get("/schedulers/expired_action_count", status_code=status.HTTP_200_OK)
def get_expired_action_count():
    try:
        return return_success(
            {
                "expired_action_count": get_dispatcher(
                    router
                ).get_expired_action_count()
            }
        )
    except Exception as e:
        raise raised_exception(f"failed to retrieve the deferred action count", e)


@router.get("/schedulers/reschedule_all", status_code=status.HTTP_200_OK)
def reschedule_all_schedulers():
    try:
        get_dispatcher(router).reschedule_all_schedulers()
        return return_success("all schedulers were successfully unscheduled")
    except Exception as e:
        raise raised_exception("failed to unschedule all schedulers", e)


@router.get("/schedulers/clear_deferred_actions", status_code=status.HTTP_200_OK)
def clear_deferred_actions():
    try:
        get_dispatcher(router).clear_all_deferred_actions()
        return return_success("deferred actions were cleared")
    except Exception as e:
        raise raised_exception("failed to clear deferred actions", e)


@router.get("/schedulers/clear_expired_actions", status_code=status.HTTP_200_OK)
def clear_expired_actions():
    try:
        get_dispatcher(router).clear_all_expired_actions()
        return return_success("expired actions were cleared")
    except Exception as e:
        raise raised_exception("failed to clear expired actions", e)


@router.get(
    "/schedulers/{scheduler_name}/actions/{action_name}", status_code=status.HTTP_200_OK
)
def schedule_action(scheduler_name: str, action_name: str):
    try:
        get_dispatcher(router).schedule_action(
            scheduler_name=scheduler_name, action_name=action_name
        )
        return return_success(
            f"action ({action_name}) was successfully scheduled ({scheduler_name})"
        )
    except Exception as e:
        raise raised_exception(
            f"failed to schedule ({scheduler_name}) action ({action_name})", e
        )

@router.get(
    "/schedulers/{scheduler_name}/actions/{action_name}/unschedule", status_code=status.HTTP_200_OK
)
def unschedule_scheduler_action(scheduler_name: str, action_name: str):
    try:
        get_dispatcher(router).unschedule_scheduler_action(
            scheduler_name=scheduler_name, action_name=action_name
        )
        return return_success(
            f"action ({action_name}) was successfully unscheduled ({scheduler_name})"
        )
    except Exception as e:
        raise raised_exception(
            f"failed to unschedule ({scheduler_name}) action ({action_name})", e
        )


@router.post(
    "/schedulers/{scheduler_name}/actions/{action_name}/defer", status_code=status.HTTP_200_OK
)
def defer_action(scheduler_name: str, action_name: str, wait_until: util.DateTime):
    try:
        get_dispatcher(router).defer_action(
            scheduler_name=scheduler_name,
            action_name=action_name,
            wait_until=wait_until.date_time,
        )
        return return_success(
            f"action ({action_name}) under ({scheduler_name}) was deferred until ({wait_until})"
        )
    except Exception as e:
        raise raised_exception(
            f"failed to defer action ({action_name}) under ({scheduler_name})", e
        )

@router.post(
    "/schedulers/{scheduler_name}/actions/{action_name}/expire", status_code=status.HTTP_200_OK
)
def expire_action(scheduler_name: str, action_name: str, expire_on: util.DateTime):
    try:
        get_dispatcher(router).expire_action(
            scheduler_name=scheduler_name,
            action_name=action_name,
            expire_on= expire_on.date_time,
        )
        return return_success(
            f"action ({action_name}) under ({scheduler_name}) will expire ({expire_on})"
        )
    except Exception as e:
        raise raised_exception(
            f"failed to expire action ({action_name}) under ({scheduler_name})", e
        )


@router.get("/schedulers/{scheduler_name}", status_code=status.HTTP_200_OK)
def get_scheduler(scheduler_name: str):
    try:
        scheduler = get_dispatcher(router).get_scheduler(scheduler_name=scheduler_name)
        return return_success(scheduler)
    except Exception as e:
        raise raised_exception(
            f"failed to retrieve the scheduler ({scheduler_name})", e
        )


@router.post("/schedulers/{scheduler_name}", status_code=status.HTTP_200_OK)
def add_scheduler(scheduler_name: str, scheduler=Depends(resolve_scheduler)):
    try:
        assert scheduler, f"couldn't resolve class for scheduler ({scheduler_name})"
        get_dispatcher(router).add_scheduler(
            scheduler_name=scheduler_name, scheduler=scheduler
        )
        return return_success(f"scheduler ({scheduler_name}) was successfully added")
    except Exception as e:
        raise raised_exception(f"failed to add scheduler ({scheduler_name})", e)


@router.put("/schedulers/{scheduler_name}", status_code=status.HTTP_200_OK)
def set_scheduler(scheduler_name: str, scheduler=Depends(resolve_scheduler)):
    try:
        assert scheduler, f"couldn't resolve class for scheduler ({scheduler_name})"
        get_dispatcher(router).set_scheduler(
            scheduler_name=scheduler_name, scheduler=scheduler
        )
        return return_success(f"scheduler ({scheduler_name}) was successfully updated")
    except Exception as e:
        raise raised_exception(f"failed to update scheduler ({scheduler_name})", e)


@router.delete("/schedulers/{scheduler_name}", status_code=status.HTTP_200_OK)
def delete_scheduler(scheduler_name: str):
    try:
        get_dispatcher(router).delete_scheduler(scheduler_name=scheduler_name)
        return return_success(f"scheduler ({scheduler_name}) was successfully deleted")
    except Exception as e:
        raise raised_exception(f"failed to delete scheduler ({scheduler_name})", e)


@router.get("/schedulers/{scheduler_name}/execute", status_code=status.HTTP_200_OK)
def execute_scheduler_actions(scheduler_name: str):
    try:
        result = get_dispatcher(router).execute_scheduler_actions(
            scheduler_name=scheduler_name
        )
        return return_success(
            {
                "msg": f"scheduler ({scheduler_name}) actions were successfully executed",
                "result": result,
            }
        )
    except Exception as e:
        raise raised_exception(
            f"failed to execute scheduler ({scheduler_name}) actions", e
        )


@router.get("/schedulers/{scheduler_name}/unschedule", status_code=status.HTTP_200_OK)
def unschedule_scheduler(scheduler_name: str):
    try:
        get_dispatcher(router).unschedule_scheduler(scheduler_name=scheduler_name)
        return return_success(
            f"scheduler ({scheduler_name}) was successfully unscheduled"
        )
    except Exception as e:
        raise raised_exception(f"failed to unschedule scheduler ({scheduler_name})", e)


@router.get("/schedulers/{scheduler_name}/reschedule", status_code=status.HTTP_200_OK)
def reschedule_scheduler(scheduler_name: str):
    try:
        get_dispatcher(router).reschedule_scheduler(scheduler_name=scheduler_name)
        return return_success(
            f"scheduler ({scheduler_name}) was successfully rescheduled"
        )
    except Exception as e:
        raise raised_exception(f"failed to reschedule scheduler ({scheduler_name})", e)
