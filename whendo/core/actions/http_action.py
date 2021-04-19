import requests
import logging
import json
from typing import Optional, Dict, Set
from whendo.core.action import Action
import whendo.core.util as util_x
from whendo.core.hooks import DispatcherHooks
from whendo.core.server import Server
from whendo.core.util import KeyTagMode


logger = logging.getLogger(__name__)


class SendPayload(Action):
    """
    This class sends a payload dictionary to a url.
    """

    url: str
    payload: Optional[dict]

    def description(self):
        return f"This action sends the supplied dictionary payload to ({self.url})."

    def execute(self, tag: str = None, data: dict = None):
        if self.payload:
            payload = self.payload.copy()
            if data:
                payload.update(data)
        elif data:
            payload = data
        else:
            payload = {"result": "no payload"}
        response = requests.post(self.url, payload)
        if response.status_code != requests.codes.ok:
            raise Exception(response)
        return self.action_result(result=response.json(), data=data)


class ExecuteAction(Action):
    """
    Execute an action at host:port.
    """

    host: str
    port: int
    action_name: str

    def description(self):
        return f"This action executes ({self.action_name}) at host:port ({self.host}:{self.port}) using the supplied data argument if provided."

    def execute(self, tag: str = None, data: dict = None):
        if data:
            if self.host == self.local_host() and self.port == self.local_port():
                # execute locally
                result = DispatcherHooks.get_action(self.action_name).execute(
                    tag=tag, data=data
                )
            else:
                result = util_x.Http(host=self.host, port=self.port).post_dict(
                    f"/actions/{self.action_name}/execute", data
                )
        else:
            if self.host == self.local_host() and self.port == self.local_port():
                # execute locally
                result = DispatcherHooks.get_action(self.action_name).execute(tag=tag)
            else:
                result = util_x.Http(host=self.host, port=self.port).get(
                    f"/actions/{self.action_name}/execute"
                )
        return self.action_result(result=result, data=data)


# class ExecuteActionServer(Action):
#     """
#     Execute an action at server.
#     """

#     server_name: str
#     action_name: str

#     def description(self):
#         return f"This action executes ({self.action_name}) at the server ({self.server_name}) using the supplied data argument if provided."

#     def execute(self, tag: str = None, data: dict = None):
#         server = DispatcherHooks.get_server(server_name=self.server_name)
#         if data:
#             if server.host == self.local_host() and server.port == self.local_port():
#                 # execute locally
#                 result = DispatcherHooks.get_action(self.action_name).execute(
#                     tag=tag, data=data
#                 )
#             else:
#                 result = util_x.Http(host=server.host, port=server.port).post_dict(
#                     f"/actions/{self.action_name}/execute", data
#                 )
#         else:
#             if server.host == self.local_host() and server.port == self.local_port():
#                 # execute locally
#                 result = DispatcherHooks.get_action(self.action_name).execute(tag=tag)
#             else:
#                 result = util_x.Http(host=server.host, port=server.port).get(
#                     f"/actions/{self.action_name}/execute"
#                 )
#         return self.action_result(result=result, data=data)


# class ExecuteActionServersKeyTag(Action):
#     """
#     Execute an action at servers. If server_key_tag is not provided, executes action at all servers.
#     """

#     action_name: str
#     server_key_tags: Optional[Dict[str, Set[str]]] = None
#     key_tag_mode: KeyTagMode = KeyTagMode.ANY

#     def description(self):
#         return f"This action executes ({self.action_name}) at the servers with key:tags satisfying ({self.server_key_tags}) using key tag mode ({self.key_tag_mode}) and using the supplied data argument if provided."

#     def execute(self, tag: str = None, data: dict = None):
#         if self.server_key_tags:
#             servers = DispatcherHooks.get_servers_by_tags(
#                 server_key_tags=self.server_key_tags, key_tag_mode=self.key_tag_mode
#             )
#         else:
#             servers = DispatcherHooks.get_servers()
#         result = []
#         if data:
#             for server in servers:
#                 if (
#                     server.host == self.local_host()
#                     and server.port == self.local_port()
#                 ):
#                     # execute locally
#                     result.append(
#                         DispatcherHooks.get_action(self.action_name).execute(
#                             tag=tag, data=data
#                         )
#                     )
#                 else:
#                     result.append(
#                         util_x.Http(host=server.host, port=server.port).post_dict(
#                             f"/actions/{self.action_name}/execute", data
#                         )
#                     )
#         else:
#             for server in servers:
#                 if (
#                     server.host == self.local_host()
#                     and server.port == self.local_port()
#                 ):
#                     # execute locally
#                     result.append(
#                         DispatcherHooks.get_action(self.action_name).execute(tag=tag)
#                     )
#                 else:
#                     result.append(
#                         util_x.Http(host=server.host, port=server.port).get(
#                             f"/actions/{self.action_name}/execute"
#                         )
#                     )
#         return self.action_result(result=result, data=data)
