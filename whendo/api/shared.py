"""
This code in this module is used in FastAPI and APIRouter code.
"""
from fastapi import status, HTTPException, APIRouter
from whendo.core.dispatcher import Dispatcher
from whendo.core.util import Now

def return_success(obj:object):
    """
    for successful returns
    """
    return obj

def raised_exception(text:str, exception:Exception):
    """
    for exception reporting
    """
    status_code = status.HTTP_400_BAD_REQUEST
    detail = {'outcome':text, 'exception': str(exception), 'time':Now.s()}
    return HTTPException(status_code=status_code, detail=detail)

# these functions enabling the passing down of singletons to routers from the main app
def get_dispatcher(router:APIRouter):
    return router.__dict__['_dispatcher']

def set_dispatcher(router:APIRouter, dispatcher:Dispatcher):
    router.__dict__['_dispatcher'] = dispatcher
    return router