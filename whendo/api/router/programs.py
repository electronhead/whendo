from fastapi import APIRouter, status, Depends
from whendo.core.util import DateTime2
from whendo.api.shared import return_success, raised_exception, get_dispatcher
from whendo.core.resolver import resolve_program

router = APIRouter(prefix="/programs", tags=["Programs"])


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
def schedule_program(program_name: str, datetime2: DateTime2):
    try:
        dt1 = datetime2.dt1
        dt2 = datetime2.dt2
        get_dispatcher(router).schedule_program(
            program_name=program_name, start=dt1, stop=dt2
        )
        return return_success(f"program ({program_name}) was successfully scheduled")
    except Exception as e:
        raise raised_exception("failed to schedule program (program_name)", e)
