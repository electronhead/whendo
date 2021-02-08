from fastapi import APIRouter, status
from app.shared import return_success, raised_exception, get_continuous

router = APIRouter(
    prefix="/jobs",
    tags=['Jobs']
)

@router.get('/start', status_code=status.HTTP_200_OK)
def start_scheduled_jobs():
    try:
        assert not get_continuous(router).is_running(), "should not be running when trying to start"
        get_continuous(router).run_continuously()
        return return_success("started running")
    except Exception as e:
        raise raised_exception("failed to start running", e)

@router.get('/stop', status_code=status.HTTP_200_OK)
def stop_scheduled_jobs():
    try:
        assert get_continuous(router).is_running(), "should be running when trying to stop"
        get_continuous(router).stop_running_continuously()
        return return_success("stopped running")
    except Exception as e:
        raise raised_exception("failed to stop running", e)

@router.get('/count', status_code=status.HTTP_200_OK)
def job_count():
    try:
        return return_success({'job_count':get_continuous(router).job_count()})
    except Exception as e:
        raise raised_exception("failed to get job count", e)