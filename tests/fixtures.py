"""
pytest fixtures for unit testing
"""

import pytest
from whendo.api import main_temp
from .uvicorn_server import UvicornTestServer


@pytest.fixture
def port(unused_tcp_port):
    """ returns an unused tcp port """
    return unused_tcp_port


@pytest.fixture
def host():
    """ the host used in unit tests """
    return "127.0.0.1"


@pytest.fixture
async def startup_and_shutdown_uvicorn(host, port):
    """Start server as test fixture and tear down after test"""
    uvicorn_server = UvicornTestServer(app=main_temp.app, host=host, port=port)
    await uvicorn_server.up()
    yield
    await uvicorn_server.down()


@pytest.fixture
def base_url(host, port):
    """ base url for unit test invocation of api """
    return f"http://{host}:{port}"
