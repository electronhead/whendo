from fastapi import APIRouter, status
from whendo.api.shared import return_success, raised_exception, get_mothership
from whendo.core.util import FilePathe

router = APIRouter(
    prefix="/mothership",
    tags = ['Mothership']
)

@router.get('/clear', status_code=status.HTTP_200_OK)
def clear_mothership():
    try:
        get_mothership(router).clear_all()
        return return_success("mothership cleared")
    except Exception as e:
        raise raised_exception("failed to clear the Mothership", e)

@router.get('/load', status_code=status.HTTP_200_OK)
def load():
    try:
        return return_success(get_mothership(router).load_current())
    except Exception as e:
        raise raised_exception("failed to retrieve the Mothership", e)

@router.get('/save', status_code=status.HTTP_200_OK)
def save():
    try:
        get_mothership(router).save_current()
        return return_success(f"mothership saved to current")
    except Exception as e:
        raise raised_exception("failed to save the Mothership", e)

@router.get('/load_from_name/{name}', status_code=status.HTTP_200_OK)
def load_from_name(name:str):
    try:
        return return_success(get_mothership(router).load_from_name(name))
    except Exception as e:
        raise raised_exception(f"failed to retrieve the Mothership from ({name})", e)

@router.get('/save_to_name/{name}', status_code=status.HTTP_200_OK)
def save_to_name(name:str):
    try:
        get_mothership(router).save_to_name(name)
        return return_success(f"mothership saved to ({name})")
    except Exception as e:
        raise raised_exception(f"failed to save the Mothership to ({name})", e)

@router.put('/saved_dir', status_code=status.HTTP_200_OK)
def set_saved_dir(file_pathe:FilePathe):
    try:
        saved_dir = file_pathe.path
        get_mothership(router).set_saved_dir(saved_dir)
        return return_success(f"saved_dir set to ({saved_dir})")
    except Exception as e:
        raise raised_exception("failed to set (saved_dir)", e)

@router.get('/saved_dir', status_code=status.HTTP_200_OK)
def get_saved_dir():
    try:
        saved_dir = get_mothership(router).get_saved_dir()
        file_pathe = FilePathe(path=saved_dir)
        return return_success(file_pathe)
    except Exception as e:
        raise raised_exception("failed to get (saved_dir)", e)