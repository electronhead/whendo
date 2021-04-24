import pytest
import whendo.core.util as util
import whendo.core.server as srv


def test_server_has_key_tag_1(servers):
    server1, server2 = servers()
    assert server1.has_key_tag("foo", "baz")


def test_server_has_key_tag_2(servers):
    server1, server2 = servers()
    server1.delete_key("foo")
    assert not server1.has_key_tag("foo", "baz")


def test_server_has_key(servers):
    server1, server2 = servers()
    server1.delete_tag("standdown")
    assert not server1.has_key("fleas")


def test_server_has_tag(servers):
    server1, server2 = servers()
    assert not server1.has_key("baz")


def test_server_delete_key_tag(servers):
    server1, server2 = servers()
    server1.delete_key_tag("foo", "baz")
    assert not server1.has_key_tag("foo", "baz")


def test_server_get_tags_by_key(servers):
    server1, server2 = servers()
    print(server1)
    assert set(server1.get_tags_by_key("foo")) == {"bar", "baz"}


def test_server_get_keys_all_1(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ALL
    assert len(server1.get_keys(tags=["bar", "baz"], key_tag_mode=mode)) > 0


def test_server_get_keys_all_2(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ALL
    assert len(server1.get_keys(tags=["bar"], key_tag_mode=mode)) == 0


def test_server_get_keys_any_1(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ANY
    assert len(server1.get_keys(tags=["bar", "baz"], key_tag_mode=mode)) > 0


def test_server_get_keys_any_2(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ANY
    assert len(server1.get_keys(tags=["bar"], key_tag_mode=mode)) > 0


def test_server_get_keys_any_3(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ANY
    assert len(server1.get_keys(tags=set(), key_tag_mode=mode)) == 0


def test_server_multiple_any_1(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ANY
    server_key_tags = {"foo": ["bar", "baz"]}
    result = []
    for server in [server1, server2]:
        for key in server_key_tags:
            tags = server_key_tags[key]
            if key in server.get_keys(tags=tags, key_tag_mode=mode):
                result.append(server)
    assert len(result) == 2


def test_server_multiple_any_2(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ANY
    server_key_tags = {"foo": ["bar"]}
    result = []
    for server in [server1, server2]:
        for key in server_key_tags:
            tags = server_key_tags[key]
            if key in server.get_keys(tags=tags, key_tag_mode=mode):
                result.append(server)
    assert len(result) == 2


def test_server_multiple_any_3(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ANY
    server_key_tags = {"foo": ["clap"]}
    result = []
    for server in [server1, server2]:
        for key in server_key_tags:
            tags = server_key_tags[key]
            if key in server.get_keys(tags=tags, key_tag_mode=mode):
                result.append(server)
    assert len(result) == 0


def test_server_multiple_any_4(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ANY
    server_key_tags = {"foo": []}
    result = []
    for server in [server1, server2]:
        for key in server_key_tags:
            tags = server_key_tags[key]
            if key in server.get_keys(tags=tags, key_tag_mode=mode):
                result.append(server)
    assert len(result) == 0


def test_server_multiple_and_1(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ALL
    server_key_tags = {"foo": ["bar", "baz"]}
    result = []
    for server in [server1, server2]:
        for key in server_key_tags:
            tags = server_key_tags[key]
            if key in server.get_keys(tags=tags, key_tag_mode=mode):
                result.append(server)
    assert len(result) == 2


def test_server_multiple_and_2(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ALL
    server_key_tags = {"foo": ["bar"]}
    result = []
    for server in [server1, server2]:
        for key in server_key_tags:
            tags = server_key_tags[key]
            if key in server.get_keys(tags=tags, key_tag_mode=mode):
                result.append(server)
    assert len(result) == 1


def test_server_multiple_and_3(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ALL
    server_key_tags = {"foo": ["clap"]}
    result = []
    for server in [server1, server2]:
        for key in server_key_tags:
            tags = server_key_tags[key]
            if key in server.get_keys(tags=tags, key_tag_mode=mode):
                result.append(server)
    assert len(result) == 0


def test_server_multiple_and_4(servers):
    server1, server2 = servers()
    mode = util.KeyTagMode.ALL
    server_key_tags = {"foo": []}
    result = []
    for server in [server1, server2]:
        for key in server_key_tags:
            tags = server_key_tags[key]
            if key in server.get_keys(tags=tags, key_tag_mode=mode):
                result.append(server)
    assert len(result) == 0


@pytest.fixture
def servers():
    def stuff():
        server1 = srv.Server(host="localhost", port=8000)
        server1.add_key_tag("foo", "bar")
        server1.add_key_tag("foo", "baz")
        server1.add_key_tag("fleas", "standdown")
        server1.add_key_tag("krimp", "kramp")
        server2 = srv.Server(host="localhost", port=8000)
        server2.add_key_tag("foo", "bar")
        server2.add_key_tag("fleas", "riseup")
        server2.add_key_tag("slip", "slide")
        return (server1, server2)

    return stuff
