from fastapi import APIRouter, status, Depends
from whendo.core.util import KeyTagMode
from whendo.api.shared import return_success, raised_exception, get_dispatcher
from whendo.core.resolver import resolve_server, resolve_rez, resolve_action
from whendo.core.action import RezDict

router = APIRouter(prefix="/servers", tags=["Servers"])


@router.get("/{server_name}", status_code=status.HTTP_200_OK)
def get_server(server_name: str):
    try:
        server = get_dispatcher(router).get_server(server_name=server_name)
        return return_success(server)
    except Exception as e:
        raise raised_exception(f"failed to retrieve the server ({server_name})", e)


@router.get("", status_code=status.HTTP_200_OK)
def get_servers():
    try:
        servers = get_dispatcher(router).get_servers()
        return return_success(servers)
    except Exception as e:
        raise raised_exception(f"failed to retrieve servers", e)


@router.post("/{server_name}", status_code=status.HTTP_200_OK)
def add_server(server_name: str, server=Depends(resolve_server)):
    try:
        assert server, f"couldn't resolve class for server ({server_name})"
        get_dispatcher(router).add_server(server_name=server_name, server=server)
        return return_success(f"server ({server_name}) was successfully added")
    except Exception as e:
        raise raised_exception(f"failed to add server ({server_name})", e)


@router.put("/{server_name}", status_code=status.HTTP_200_OK)
def set_server(server_name: str, server=Depends(resolve_server)):
    try:
        assert server, f"couldn't resolve class for server ({server_name})"
        get_dispatcher(router).set_server(server_name=server_name, server=server)
        return return_success(f"server ({server_name}) was successfully updated")
    except Exception as e:
        raise raised_exception(f"failed to update server ({server_name})", e)


@router.delete("/{server_name}", status_code=status.HTTP_200_OK)
def delete_server(server_name: str):
    try:
        get_dispatcher(router).delete_server(server_name=server_name)
        return return_success(f"server ({server_name}) was successfully deleted")
    except Exception as e:
        raise raised_exception(f"failed to delete server ({server_name})", e)


@router.get("/{server_name}/describe", status_code=status.HTTP_200_OK)
def describe_server(server_name: str):
    try:
        return get_dispatcher(router).describe_server(server_name=server_name)
    except Exception as e:
        raise raised_exception(f"failed to describe program ({server_name})", e)


@router.post("/{server_name}/add_key_tags", status_code=status.HTTP_200_OK)
def add_server_key_tags(server_name: str, key_tags: dict):
    try:
        get_dispatcher(router).add_server_key_tags(
            server_name=server_name, key_tags=key_tags
        )
        return return_success(
            f"key tags ({key_tags}) were successfully added to server ({server_name})."
        )
    except Exception as e:
        raise raised_exception(
            f"failed to add key-tags ({key_tags}) to server ({server_name}))", e
        )


@router.get("/{server_name}/get_tags", status_code=status.HTTP_200_OK)
def get_server_tags(server_name: str):
    try:
        return get_dispatcher(router).get_server_tags(server_name=server_name)
    except Exception as e:
        raise raised_exception(f"failed to retrieve tags for server ({server_name})", e)


@router.post("/by_tags/{mode}", status_code=status.HTTP_200_OK)
def get_servers_by_tags(mode: str, key_tags: dict):
    try:
        return get_dispatcher(router).get_servers_by_tags(
            key_tags=key_tags, key_tag_mode=KeyTagMode(mode)
        )
    except Exception as e:
        raise raised_exception(
            f"failed to get servers by key-tags ({key_tags}) using mode ({mode}))", e
        )


@router.get(
    "/{server_name}/actions/{action_name}/execute", status_code=status.HTTP_200_OK
)
def execute_on_server(server_name: str, action_name: str):
    try:
        return get_dispatcher(router).execute_on_server(
            server_name=server_name, action_name=action_name
        )
    except Exception as e:
        raise raised_exception(
            f"failed to get execute action ({action_name}) on server ({server_name})", e
        )


@router.post(
    "/{server_name}/actions/{action_name}/execute_with_rez",
    status_code=status.HTTP_200_OK,
)
def execute_on_server_with_rez(
    server_name: str, action_name: str, rez=Depends(resolve_rez)
):
    try:
        return get_dispatcher(router).execute_on_server_with_rez(
            server_name=server_name, action_name=action_name, rez=rez
        )
    except Exception as e:
        raise raised_exception(
            f"failed to execute action ({action_name}) on server ({server_name}) using rez ({rez})",
            e,
        )


@router.post(
    "/by_tags/{mode}/actions/{action_name}/execute", status_code=status.HTTP_200_OK
)
def execute_on_servers(action_name: str, mode: str, key_tags: dict):
    try:
        return get_dispatcher(router).execute_on_servers(
            action_name=action_name,
            key_tags=key_tags,
            key_tag_mode=KeyTagMode(mode),
        )
    except Exception as e:
        raise raised_exception(
            f"failed to execute action ({action_name}) by key tags ({key_tags})", e
        )


@router.post(
    "/by_tags/{mode}/actions/{action_name}/execute_with_rez",
    status_code=status.HTTP_200_OK,
)
def execute_on_servers_with_rez(
    action_name: str, mode: str, rez_dict=Depends(resolve_action)
):
    try:
        rez = rez_dict.rez
        key_tags = rez_dict.dictionary
        return get_dispatcher(router).execute_on_servers_with_rez(
            action_name=action_name,
            key_tags=key_tags,
            key_tag_mode=KeyTagMode(mode),
            rez=rez,
        )
    except Exception as e:
        raise raised_exception(
            f"failed to execute action ({action_name}) by rez-dict ({rez_dict})", e
        )
