from fastapi import APIRouter, status, Depends
from whendo.core.util import DateTime2
from whendo.api.shared import return_success, raised_exception, get_dispatcher
from whendo.core.resolver import resolve_program

router = APIRouter(prefix="/programs", tags=["Programs"])


@router.get("/deferred_program_count", status_code=status.HTTP_200_OK)
def get_expiring_action_count():
    try:
        return return_success(
            {
                "deferred_program_count": get_dispatcher(
                    router
                ).get_deferred_program_count()
            }
        )
    except Exception as e:
        raise raised_exception(f"failed to retrieve the deferred program count", e)


@router.get("/clear_deferred_programs", status_code=status.HTTP_200_OK)
def clear_deferred_actions():
    try:
        get_dispatcher(router).clear_all_deferred_programs()
        return return_success("deferred programs were cleared")
    except Exception as e:
        raise raised_exception("failed to clear deferred programs", e)


@router.get("/{program_name}", status_code=status.HTTP_200_OK)
def get_program(program_name: str):
    try:
        program = get_dispatcher(router).get_program(program_name=program_name)
        return return_success(program)
    except Exception as e:
        raise raised_exception(f"failed to retrieve the program ({program_name})", e)


@router.post("/{program_name}", status_code=status.HTTP_200_OK)
def add_program(program_name: str, program=Depends(resolve_program)):
    try:
        assert program, f"couldn't resolve class for program ({program_name})"
        get_dispatcher(router).add_program(program_name=program_name, program=program)
        return return_success(f"program ({program_name}) was successfully added")
    except Exception as e:
        raise raised_exception(f"failed to add program ({program_name})", e)


@router.put("/{program_name}", status_code=status.HTTP_200_OK)
def set_program(program_name: str, program=Depends(resolve_program)):
    try:
        assert program, f"couldn't resolve class for program ({program_name})"
        get_dispatcher(router).set_program(program_name=program_name, program=program)
        return return_success(f"program ({program_name}) was successfully updated")
    except Exception as e:
        raise raised_exception(f"failed to update program ({program_name})", e)


@router.delete("/{program_name}", status_code=status.HTTP_200_OK)
def delete_program(program_name: str):
    try:
        get_dispatcher(router).delete_program(program_name=program_name)
        return return_success(f"program ({program_name}) was successfully deleted")
    except Exception as e:
        raise raised_exception(f"failed to delete program ({program_name})", e)


@router.get("/{program_name}/describe", status_code=status.HTTP_200_OK)
def describe_program(program_name: str):
    try:
        return get_dispatcher(router).describe_program(program_name=program_name)
    except Exception as e:
        raise raised_exception(f"failed to describe program ({program_name})", e)


@router.post("/{program_name}/schedule", status_code=status.HTTP_200_OK)
def schedule_program(program_name: str, start_stop: DateTime2):
    try:
        get_dispatcher(router).schedule_program(
            program_name=program_name, start=start_stop.dt1, stop=start_stop.dt2
        )
        return return_success(f"program ({program_name}) was successfully scheduled")
    except Exception as e:
        raise raised_exception(f"failed to schedule program ({program_name})", e)


@router.get("/{program_name}/unschedule", status_code=status.HTTP_200_OK)
def unschedule_program(program_name: str):
    try:
        get_dispatcher(router).unschedule_program(program_name=program_name)
        return return_success(f"program ({program_name}) was successfully unscheduled")
    except Exception as e:
        raise raised_exception(f"failed to schedule program ({program_name})", e)
