from fastapi import FastAPI
import asyncio
import uvicorn
from typing import Optional, List

class UvicornTestServer(uvicorn.Server):
    """Uvicorn test server

    This class is slight adaptation of the result of the discussion in this github thread...

        https://github.com/miguelgrinberg/python-socketio/issues/332#issuecomment-712928157

    Usage:
        @pytest.fixture
        async def start_stop_server():
            server = UvicornTestServer()
            await server.up()
            yield
            await server.down()
        
    Note:
        The fixture mechanism calls the above fixture twice. Once at the beginning of the
        relevant test function, and once at the exit of the test function. The yield
        basically splits the execution into two parts: setup and teardown. The fixtures
        package and the people who used fixtures to build this class are awesome.
    """

    def __init__(self, app: FastAPI, host: str, port: int, workers=1):
        """
        Create a Uvicorn test server for use as a pytest fixture
        """
        self._startup_done = asyncio.Event()
        super().__init__(config=uvicorn.Config(app, host=host, port=port, workers=1))

    async def startup(self, sockets: Optional[List] = None) -> None:
        """Override uvicorn startup"""
        await super().startup(sockets=sockets)
        self.config.setup_event_loop()
        self._startup_done.set()

    async def up(self) -> None:
        """Start up server asynchronously"""
        self._serve_task = asyncio.create_task(self.serve())
        await self._startup_done.wait()

    async def down(self) -> None:
        """Shut down server asynchronously"""
        self.should_exit = True
        await self._serve_task