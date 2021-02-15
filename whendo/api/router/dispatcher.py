from fastapi import APIRouter, status
from whendo.api.shared import return_success, raised_exception, get_dispatcher
from whendo.core.util import FilePathe

router = APIRouter(
    prefix="/dispatcher",
    tags = ['Dispatcher']
)

@router.get('/clear', status_code=status.HTTP_200_OK)
def clear_dispatcher():
    try:
        get_dispatcher(router).clear_all()
        return return_success("dispatcher cleared")
    except Exception as e:
        raise raised_exception("failed to clear the Dispatcher", e)

@router.get('/load', status_code=status.HTTP_200_OK)
def load():
    try:
        return return_success(get_dispatcher(router).load_current())
    except Exception as e:
        raise raised_exception("failed to retrieve the Dispatcher", e)

@router.get('/save', status_code=status.HTTP_200_OK)
def save():
    try:
        get_dispatcher(router).save_current()
        return return_success(f"dispatcher saved to current")
    except Exception as e:
        raise raised_exception("failed to save the Dispatcher", e)

@router.get('/load_from_name/{name}', status_code=status.HTTP_200_OK)
def load_from_name(name:str):
    try:
        return return_success(get_dispatcher(router).load_from_name(name))
    except Exception as e:
        raise raised_exception(f"failed to retrieve the Dispatcher from ({name})", e)

@router.get('/save_to_name/{name}', status_code=status.HTTP_200_OK)
def save_to_name(name:str):
    try:
        get_dispatcher(router).save_to_name(name)
        return return_success(f"dispatcher saved to ({name})")
    except Exception as e:
        raise raised_exception(f"failed to save the Dispatcher to ({name})", e)

@router.put('/saved_dir', status_code=status.HTTP_200_OK)
def set_saved_dir(file_pathe:FilePathe):
    try:
        saved_dir = file_pathe.path
        get_dispatcher(router).set_saved_dir(saved_dir)
        return return_success(f"saved_dir set to ({saved_dir})")
    except Exception as e:
        raise raised_exception("failed to set (saved_dir)", e)

@router.get('/saved_dir', status_code=status.HTTP_200_OK)
def get_saved_dir():
    try:
        saved_dir = get_dispatcher(router).get_saved_dir()
        file_pathe = FilePathe(path=saved_dir)
        return return_success(file_pathe)
    except Exception as e:
        raise raised_exception("failed to get (saved_dir)", e)