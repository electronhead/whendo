from fastapi import APIRouter, status, Depends
from whendo.core.util import DateTime2, KeyTagMode
from whendo.api.shared import return_success, raised_exception, get_dispatcher
from whendo.core.resolver import resolve_server

router = APIRouter(prefix="/servers", tags=["Servers"])


@router.get("/{server_name}", status_code=status.HTTP_200_OK)
def get_server(server_name: str):
    try:
        return get_dispatcher(router).get_server(server_name=server_name)
    except Exception as e:
        raise raised_exception(f"failed to retrieve the server ({server_name})", e)


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


@router.get("/{server_name}/execute/{action_name}", status_code=status.HTTP_200_OK)
def execute_on_server(server_name: str, action_name: str):
    try:
        return get_dispatcher(router).execute_on_server(
            server_name=server_name, action_name=action_name
        )
    except Exception as e:
        raise raised_exception(
            f"failed to get execute action ({action_name}) on server ({server_name})", e
        )


@router.post("/{server_name}/execute/{action_name}", status_code=status.HTTP_200_OK)
def execute_on_server_with_data(server_name: str, action_name: str, data: dict):
    try:
        return get_dispatcher(router).execute_on_server_with_data(
            server_name=server_name, action_name=action_name, data=data
        )
    except Exception as e:
        raise raised_exception(
            f"failed to get execute action ({action_name}) on server ({server_name})", e
        )


@router.post("/execute_by_tags/{mode}/{action_name}", status_code=status.HTTP_200_OK)
def execute_on_servers(action_name: str, mode: str, key_tags: dict):
    try:
        return get_dispatcher(router).execute_on_servers(
            action_name=action_name,
            key_tags=key_tags,
            key_tag_mode=KeyTagMode(mode),
        )
    except Exception as e:
        raise raised_exception(
            f"failed to get servers by key-tags ({key_tags}) using mode ({mode}))", e
        )


@router.post(
    "/execute_by_tags_with_data/{mode}/{action_name}", status_code=status.HTTP_200_OK
)
def execute_by_tags_with_data(action_name: str, mode: str, key_tags: dict, data: dict):
    try:
        return get_dispatcher(router).execute_on_servers_with_data(
            action_name=action_name,
            key_tags=key_tags,
            key_tag_mode=KeyTagMode(mode),
            data=data,
        )
    except Exception as e:
        raise raised_exception(
            f"failed to get servers by key-tags ({key_tags}) using mode ({mode}))", e
        )
