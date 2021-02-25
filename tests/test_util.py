from datetime import datetime, timedelta
import os
import pathlib
from pydantic import BaseModel
from typing import List
import whendo.core.util as util


def test_now_1():
    now1 = datetime.now()
    now2 = util.Now.dt()
    elapsed = now2 - now1
    assert elapsed < timedelta(microseconds=100.0)


def test_now_2():
    now = datetime.now()
    now2 = util.Now.t()
    date2 = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now2.hour,
        minute=now2.minute,
        second=now2.second,
        microsecond=now2.microsecond,
    )
    elapsed = date2 - now
    assert elapsed < timedelta(microseconds=100.0)


def test_now_3():
    now1 = datetime.now().time()
    now1_str = now1.strftime("%H:%M:%S")
    now2 = util.Now.s()
    assert now1_str in now2


def test_all_visible_subclasses():
    class A:
        pass

    class B(A):
        pass

    class C(A):
        pass

    class D(B):
        pass

    x = util.all_visible_subclasses(A)
    y = {B, C, D}
    assert x == y


def test_key_strings_from_class():
    class A(BaseModel):
        a: str
        b: str

    x = {"a", "b"}
    y = util.key_strings_from_class(A)
    assert x == y


def test_key_strings_from_dict():
    x = {"a", "b"}
    y = util.key_strings_from_dict({"a": 1, "b": 2})
    assert x == y


def test_resolve_instance():
    """
    Top > A, B, D
    D > C
    """

    class Top(BaseModel):
        pass

    class C(Top):
        c: str

    class D(C):
        d: str
        d_instance: Top

    class B(Top):
        b_instance: Top
        b_list: List[Top]

    class A(Top):
        a_list: List[Top]

    dictionary0 = {"c": "why"}
    dictionary1 = {  # D
        "c": "dc",
        "d": "abc",
        "d_instance": {  # C
            "c": "mmm",
        },
    }
    dictionary2 = {  # A
        "a_list": [
            {  # B
                "b_instance": {"c": "xxx"},  # C
                "b_list": [{"c": "yyy"}, {"c": "zzz"}, dictionary1],  # C  # C
            },
            {"c": "people", "d": "who", "d_instance": dictionary0},  # D
        ]
    }
    instance0 = util.resolve_instance(Top, dictionary0)
    instance1 = util.resolve_instance(Top, dictionary1)
    instance2 = util.resolve_instance(Top, dictionary2)
    assert isinstance(instance0, C)
    assert isinstance(instance1, D)
    assert isinstance(instance2, A)
    assert isinstance(instance2.a_list[0].b_instance, C)
    assert instance1 == instance2.a_list[0].b_list[2]
    assert instance0 == instance2.a_list[1].d_instance


def test_filepathe():
    path = util.FilePathe(path="a/b/c")
    new_path = util.FilePathe(**(path.dict()))
    assert path.path == new_path.path, "path reconstruction failed"


def test_dirs(tmp_path):
    """
    test to make sure that files with the same name are written to
    separate directories
    """

    def assure_writes_and_reads(thunk):
        """ make sure that files can be written to and read from """
        lines = None
        file = thunk(home_path=tmp_path) + "foo.txt"
        with open(file, "w") as fid:
            fid.write("blee blee blee\n")
        with open(file, "r") as fid:
            lines = fid.readlines()
        assert lines is not None and isinstance(lines, list) and len(lines) >= 1
        return file

    file1 = assure_writes_and_reads(util.Dirs.saved_dir)
    file2 = assure_writes_and_reads(util.Dirs.output_dir)
    file3 = assure_writes_and_reads(util.Dirs.log_dir)
    assert file1 != file2 and file2 != file3 and file3 != file1


def test_dirs_2(tmp_path):
    try:
        file_path = os.path.join(util.Dirs.log_dir(home_path=tmp_path), "job.log")
    except:
        assert False


def test_output(tmp_path):
    file = str(tmp_path / "output.txt")
    util.Output.pprint({"what": "hmmm"}, file=file)
    lines = None
    with open(file, "r") as fid:
        lines = fid.readlines()
    assert lines is not None and isinstance(lines, list) and len(lines) >= 1


def test_shared_rw_1():
    shared = util.SharedRWs.get("foo")

    def funk(dictionary: dict):
        dictionary["a"] = 1
        return 1

    result = shared.apply(funk)
    assert result == 1
    assert isinstance(shared.data_copy(), dict)


def test_shared_rw_2():
    """
    Test transactional nature with a funky failure.
    """
    shared = util.SharedRWs.get("foo")

    def funk1(dictionary: dict):
        dictionary["a"] = 1
        return 1

    result = shared.apply(funk1)

    def funk2(dictionary: dict):
        dictionary["a"] = 2
        raise Exception("oops")

    try:
        shared.apply(funk2)
    except:
        pass
    assert shared.data_copy()["a"] == 1


def test_shared_ro_1():
    dictionary = {"a": 1}
    shared = util.SharedROs.get("foo", dictionary)
    dictionary["a"] = 3
    assert shared.data_copy()["a"] == 1


def test_system_info():
    util.SystemInfo.init(host="127.0.0.4", port=8000)
    info = util.SystemInfo.get()
    assert "host" in info
    assert info["host"] == "127.0.0.4"
    assert "port" in info
    assert info["port"] == 8000
    assert "start" in info
    assert "cwd" in info
    assert "login" in info
    assert "os_version" in info
    assert "successes" in info
    assert "failures" in info
    assert "elapsed" in info
