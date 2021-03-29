from fastapi import APIRouter, status
from whendo.api.shared import return_success, raised_exception, get_dispatcher

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/run", status_code=status.HTTP_200_OK)
def run_jobs():
    try:
        return return_success(get_dispatcher(router).run_jobs())
    except Exception as e:
        raise raised_exception("failed to start running", e)


@router.get("/stop", status_code=status.HTTP_200_OK)
def stop_jobs():
    try:
        return return_success(get_dispatcher(router).stop_jobs())
    except Exception as e:
        raise raised_exception("failed to stop running", e)


@router.get("/count", status_code=status.HTTP_200_OK)
def job_count():
    try:
        return return_success({"job_count": get_dispatcher(router).job_count()})
    except Exception as e:
        raise raised_exception("failed to get job count", e)


@router.get("/are_running", status_code=status.HTTP_200_OK)
def jobs_are_running():
    try:
        return return_success(get_dispatcher(router).jobs_are_running())
    except Exception as e:
        raise raised_exception("failed to determine if jobs are running", e)


@router.get("/clear", status_code=status.HTTP_200_OK)
def clear_jobs():
    try:
        return return_success(get_dispatcher(router).clear_jobs())
    except Exception as e:
        raise raised_exception("failed to get job count", e)
