"""
pytest fixtures for unit testing
"""

import pytest
from whendo.core.dispatcher import Dispatcher
from whendo.core.actions.file_action import FileHeartbeat
from whendo.core.schedulers.cont_scheduler import Timely
from whendo.core.continuous import Continuous
from whendo.api import main_temp
from .uvicorn_server import UvicornTestServer


@pytest.fixture
def friends(tmp_path):
    """ returns a tuple of useful test objects """

    def stuff():
        # want a fresh tuple from the fixture
        saved_dir = str(tmp_path)
        output_file = str(tmp_path / "output.txt")
        dispatcher = Dispatcher(saved_dir=saved_dir)
        dispatcher.set_continuous(Continuous())
        dispatcher.initialize()
        action = FileHeartbeat(file=output_file)
        scheduler = Timely(interval=1)

        return dispatcher, scheduler, action

    return stuff


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
