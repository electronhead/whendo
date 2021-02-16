from fastapi import APIRouter, status
from whendo.api.shared import return_success, raised_exception, get_dispatcher

router = APIRouter(
    prefix="/jobs",
    tags=['Jobs']
)

@router.get('/run', status_code=status.HTTP_200_OK)
def start_scheduled_jobs():
    try:
        assert not get_dispatcher(router).jobs_are_running(), "should not be running when trying to start"
        get_dispatcher(router).run_jobs()
        return return_success("started running")
    except Exception as e:
        raise raised_exception("failed to start running", e)

@router.get('/stop', status_code=status.HTTP_200_OK)
def stop_scheduled_jobs():
    try:
        assert get_dispatcher(router).jobs_are_running(), "should be running when trying to stop"
        get_dispatcher(router).stop_jobs()
        return return_success("stopped running")
    except Exception as e:
        raise raised_exception("failed to stop running", e)

@router.get('/count', status_code=status.HTTP_200_OK)
def job_count():
    try:
        return return_success({'job_count':get_dispatcher(router).job_count()})
    except Exception as e:
        raise raised_exception("failed to get job count", e)

@router.get('/are_running', status_code=status.HTTP_200_OK)
def jobs_are_running():
    try:
        return return_success({'job_count':get_dispatcher(router).jobs_are_running()})
    except Exception as e:
        raise raised_exception("failed to get job count", e)

@router.get('/clear', status_code=status.HTTP_200_OK)
def jobs_are_running():
    try:
        return return_success({'job_count':get_dispatcher(router).clear_jobs()})
    except Exception as e:
        raise raised_exception("failed to get job count", e)