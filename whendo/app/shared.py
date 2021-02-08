"""
This code in this module is used in FastAPI and APIRouter code.
"""
from fastapi import status, HTTPException, APIRouter
from mothership.mothership import Mothership
from mothership.continuous import Continuous
from mothership.util import Now

def return_success(dictionary:dict):
    """
    for successful returns
    """
    return dictionary

def raised_exception(text:str, exception:Exception):
    """
    for exception reporting
    """
    status_code = status.HTTP_400_BAD_REQUEST
    detail = {'outcome':text, 'exception': str(exception), 'time':Now.s()}
    return HTTPException(status_code=status_code, detail=detail)

# these functions enabling the passing down of singletons to routers from the main app
def get_mothership(router:APIRouter):
    return router.__dict__['_mothership']

def get_continuous(router:APIRouter):
    return router.__dict__['_continuous']

def set_mothership(router:APIRouter, mothership:Mothership):
    router.__dict__['_mothership'] = mothership
    return router

def set_continuous(router:APIRouter, continuous:Continuous):
    router.__dict__['_continuous'] = continuous
    return router