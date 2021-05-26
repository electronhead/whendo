try:
    from psutil import virtual_memory, net_if_addrs, cpu_percent, getloadavg
except:
    from .mockpsutil import virtual_memory, net_if_addrs, cpu_percent, getloadavg

import logging
from enum import Enum
from pprint import PrettyPrinter
from sys import stdout
import socket
import requests
import json
from datetime import datetime, time
from typing import Callable, Optional
import os
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Any
from threading import RLock

logger = logging.getLogger(__name__)

# Enums


class TimeUnit(str, Enum):
    """
    usage:
        TimeUnit.minute
    """

    day = "day"
    hour = "hour"
    minute = "minute"
    second = "second"


class KeyTagMode(str, Enum):
    ALL = "all"
    ANY = "any"


# functions


def dt_to_str(dt: datetime) -> str:
    return dt.strftime("%Y.%m.%d:%H.%M.%S")


def str_to_dt(dts: str) -> datetime:
    return datetime.strptime(dts, "%Y.%m.%d:%H.%M.%S")


def t_to_str(t: time) -> str:
    return t.isoformat(timespec="seconds")


def str_to_t(ts: str) -> time:
    return time.fromisoformat(ts)


def ip_addrs():
    """
    Returns AF_INET addresses for local computer
    """
    nia = net_if_addrs()
    return dict(
        (k, nia[k][0].address) for k in nia if nia[k][0].family == socket.AF_INET
    )


def all_visible_subclasses(klass):
    """
    Returns all reachable subclasses of the supplied class, presumably a BaseModel subclass.
    """

    def helper(klas, result):
        subklases = klas.__subclasses__()
        if len(subklases) > 0:
            result.update(subklases)
            for subklas in subklases:
                helper(subklas, result)

    result = set()
    helper(klass, result)
    return result


def key_strings_from_dict(dictionary: Dict[str, Any]):
    """
    Returns the set of keys from a dictionary.
    """
    return set(x for x in dictionary)


def key_strings_from_class(klass):
    """
    Returns the set of visible fields from a class, presumably a BaseModel subclass.
    """
    return set(x for x in klass.__fields__.keys())


def find_class(klass, dictionary: Dict[str, Any]):
    """
    Given a dictionary, find the best-fit class among the subclasses
    of the supplied class.
    """
    dictionary_keys = key_strings_from_dict(dictionary)
    classes = all_visible_subclasses(klass)
    classes.add(klass)  # the top class might not be abstract
    min_count = 100
    found_class = None
    for clas in classes:
        class_keys = key_strings_from_class(clas)
        if len(dictionary_keys - class_keys) == 0:  # make sure class has enough fields
            count = len(class_keys)
            if (
                count < min_count
            ):  # pick class with fewest fields, resulting in tightest conformance with dictionary
                found_class = clas
                min_count = count
    return found_class


def resolve_instance(
    klass, dictionary: Dict[str, Any], check_for_found_class: bool = True
):
    """
    if an (improper) subclass is found that maps to the supplied dictionary, the dictionary
    is converted to an instance of that class. If the dictionary contains lists of dictionaries,
    those dictionaries are recursively resolved.
    """
    found_class = find_class(klass, dictionary)
    if found_class is None:
        if check_for_found_class:
            raise NameError(
                f"could not resolve dictionary ({dictionary}) to a subclass of ({klass})"
            )
        else:
            return dictionary
    else:
        # resolve singleton dictionary elements; not constrained to producing instance of klass subclass
        for (key, value) in dictionary.items():
            if isinstance(value, dict):
                if (
                    key != "vals"
                ):  # HACK!!! Val.vals can have dictionary elements that intersect with other BaseModel objects
                    dictionary[key] = resolve_instance(
                        klass, dictionary=value, check_for_found_class=False
                    )
        # resolve list containing all dictionary elements; likelihood of non-klass in this circumstance
        # is very small, therefore more strict than for singletons
        for (key, value) in dictionary.items():
            if isinstance(value, list):
                if all(isinstance(element, dict) for element in value):
                    dictionary[key] = list(
                        resolve_instance(
                            klass, dictionary=element, check_for_found_class=False
                        )
                        for element in value
                    )
        try:
            return found_class(**dictionary)
        except:
            return dictionary


def resolve_instance_multi_class(
    klasses, dictionary: Dict[str, Any], check_for_found_class: bool = True
):
    """
    An also recursive version of resolve_instance that resolves across multiple
    inheritance trees.
    """
    found_classes = [
        x for x in set(find_class(klass, dictionary) for klass in klasses) if x
    ]

    count = len(found_classes)
    if count == 0:
        if check_for_found_class:
            raise NameError(
                f"could not resolve dictionary ({dictionary}) to a subclass of at least one of ({klasses})"
            )
        else:
            for (key, value) in dictionary.items():
                if isinstance(value, dict):
                    if key != "vals":  # see resolve_instance()
                        dictionary[key] = resolve_instance_multi_class(
                            klasses, dictionary=value, check_for_found_class=False
                        )
            return dictionary
    if count > 1:
        if dictionary == None or len(dictionary) == 0:
            return None
        else:
            raise NameError(
                f"multiple found classes ({found_classes}) for dictionary ({dictionary})"
            )
    else:
        found_class = found_classes[0]
        # resolve singleton dictionary elements; not constrained to producing instance of klass subclass
        for (key, value) in dictionary.items():
            if isinstance(value, dict):
                if key != "vals":  # see resolve_instance()
                    dictionary[key] = resolve_instance_multi_class(
                        klasses, dictionary=value, check_for_found_class=False
                    )
        # resolve list containing all dictionary elements; likelihood of non-klass in this circumstance
        # is very small, therefore more strict than for singletons
        for (key, value) in dictionary.items():
            if isinstance(value, list):
                if all(isinstance(element, dict) for element in value):
                    dictionary[key] = list(
                        resolve_instance_multi_class(
                            klasses, dictionary=element, check_for_found_class=False
                        )
                        for element in value
                    )
        try:
            return found_class(**dictionary)
        except:
            return dictionary


def object_info(obj):
    return {
        "class": f"{obj.__class__.__module__}.{obj.__class__.__name__}",
        "instance": obj.__dict__,
    }


def add_to_list(a_list: list, element: object):
    """
    Attempts to append element to a list. If already contained,
    returns 0. Else 1.
    """
    if element not in a_list:
        a_list.append(element)
        return 1
    return 0


# classes


class Now:
    """
    Class methods compute string, datetime and time versions of the current time.
    """

    @classmethod
    def dt(cls):
        dt, s, t, st = cls.quad()
        return dt

    @classmethod
    def s(cls):
        dt, s, t, st = cls.quad()
        return s

    @classmethod
    def t(cls):
        dt, s, t, st = cls.quad()
        return t

    @classmethod
    def st(cls):
        dt, s, t, st = cls.quad()
        return st

    @classmethod
    def quad(cls):
        dt = datetime.now()
        s = f"{dt.strftime('%H:%M:%S')} on {dt.strftime('%Y-%m-%d')}"
        t = dt.time()
        st = f"{dt.strftime('%H:%M:%S')}"
        return dt, s, t, st


class Output:
    """
    usage:
        Output.pprint(dictionary={'a', 'abc'}))
    """

    @classmethod
    def default_file(cls):
        return Dirs.output_dir() + "output.txt"

    @classmethod
    def pprint(cls, dictionary: dict, file: str = None):
        if file is None:
            file = cls.default_file()
        with open(file, "a") as outfile:
            PP.pprint(dictionary, stream=outfile)


class PP:
    """
    usage:
        PP.pprint(json_ish_object)
    note:
        could be a function, but PP asserts its global nature
    """

    @classmethod
    def pprint(cls, dictionary, indent=2, stream=stdout):
        PrettyPrinter(indent=indent, stream=stream).pprint(dictionary)


class Dirs:
    """
    This class computes directory paths for saved, output and log files. It creates the directories if absent.

    {home dir} / .whendo / cwd directory name / label /

    For example, if /home/pi/dev/whatnot/ were the current working directory, the computed directory with
    a label of 'output' would be /home/pi/.whendo/whatnot/output.

    This allows multiple whendo api servers running on a computer. That said, its important to give some thought to
    where you choose to initially run the server. You can run the server from another directory if you remember
    to move the relevant subdirectory of [{home dir}/.whendo/].

    """

    @classmethod
    def output_dir(cls, home_path: Path = None):
        return str(cls.assure_dir(cls.dir_from_label("output", home_path)))

    @classmethod
    def saved_dir(cls, home_path: Path = None):
        return str(cls.assure_dir(cls.dir_from_label("saved", home_path)))

    @classmethod
    def log_dir(cls, home_path: Path = None):
        return str(cls.assure_dir(cls.dir_from_label("log", home_path)))

    @classmethod
    def dir_from_label(cls, label: str, home_path: Path = None):
        path = home_path if home_path else Path.home()
        return str(path / ".whendo" / os.getcwd().split("/")[-1:][0] / label) + "/"

    @classmethod
    def assure_dir(cls, assured_dir: str):
        if not os.path.exists(assured_dir):
            os.makedirs(assured_dir)
        return assured_dir


class SharedRO:
    """
    This class provides in-memory shared data so that actions can communicate with each other during
    an api server's lifetime. Not meant to be persisted. Persisting shared data is a different feature.

    The point of this class is to treat the initializing dictionary as read-only data. Subsequent
    accesses always produce the same result. The contract has only one access point for the contained
    dictionary, the data_copy method.

    Instances not meant to be created directly. Use Shared_ROs.get(...) instead.

    Usage:
        sh = Shared_ROs.get('foo', some_dictionary)
        assert sh.get('foo') == some_dictionary # not identity comparison
    """

    def __init__(self, dictionary: dict):
        self.data = dictionary.copy()

    def data_copy(self):
        intermediate_result = self.data.copy()
        for key, value in intermediate_result.items():
            if isinstance(value, Callable):
                intermediate_result[key] = value()
        return intermediate_result

    def clear(self):
        self.data.clear()


class SharedRW(SharedRO):
    """
    This class provides in-memory shared data so that actions can communicate with each other during
    an api server's lifetime. Not meant to be persisted. Persisting shared data is a different feature.

    The point of this class is to treat the initializing dictionary as writeable data. Review the
    apply method, which implements a critical section with a threading.RLock. The supplied Callable
    operates on a copy of the contained dictionary.

    Instances not meant to be created directly. Use Shared_RWs.get(...) instead.

    Usage:
        sh = Shared_RWs.get('foo')
        def update(d:dict):
            d['a'] = 1
            return d['a']
        result = sh.apply(update)
        assert 1 == result
        assert sh.data.copy()['a'] == 1
    """

    def __init__(self, dictionary: dict = {}):
        super().__init__(dictionary=dictionary)
        self.lock = RLock()

    def apply(self, callable: Callable):
        """
        Transactionally applies callable to a copy of the data. A failure within
        the callable won't corrupt the dictionary.
        """
        with self.lock:
            copy = self.data.copy()
            result = callable(copy)
            self.data = copy
            return result


class SharedROs:
    """
    A dictionary of instances of SharedRO's.
    """

    singletons: Dict[str, SharedRO] = {}

    @classmethod
    def get(cls, label: str, dictionary: dict = {}) -> SharedRO:
        if label not in cls.singletons:
            cls.singletons[label] = SharedRO(dictionary=dictionary)
        return cls.singletons[label]

    @classmethod
    def key_set(cls):
        return set(cls.singletons.keys())

    @classmethod
    def clear(cls):
        cls.singletons.clear()


class SharedRWs:
    """
    A dictionary of instances of SharedWR's.
    """

    singletons: Dict[str, SharedRW] = {}

    @classmethod
    def get(cls, label: str, dictionary: dict = {}) -> SharedRW:
        if label not in cls.singletons:
            cls.singletons[label] = SharedRW(dictionary=dictionary)
        return cls.singletons[label]

    @classmethod
    def key_set(cls):
        return set(cls.singletons.keys())

    @classmethod
    def clear(cls):
        cls.singletons.clear()


class SystemInfo:
    @classmethod
    def init(cls, host: str, port: int):
        SharedRWs.clear()
        dt, s, t, st = Now.quad()
        SharedRWs.get(
            "system_info",
            {
                "host": host,
                "port": port,
                "start": s,
                "current": lambda: Now.s(),
                "elapsed": lambda: str(Now.dt() - dt),
                "successes": 0,
                "failures": 0,
                "cwd": os.getcwd(),
                "login": os.getlogin(),
                "os_version": os.uname()[3],
                "ip_addrs": ip_addrs(),
                "virtual_memory": lambda: dict(
                    zip(
                        virtual_memory()._fields,
                        ["{:,}".format(n) for n in virtual_memory()],
                    )
                ),
                "load_avg": lambda: dict(zip(["1min", "5min", "15min"], getloadavg())),
                "cpu_percent": lambda: cpu_percent(),
                "log_dir": os.path.join(Dirs.log_dir()),
            },
        )

    @classmethod
    def increment_successes(cls):
        system_info = SharedRWs.get("system_info")

        def update(dictionary: dict):
            dictionary["successes"] = 1 + dictionary["successes"]

        system_info.apply(update)

    @classmethod
    def increment_failures(cls):
        system_info = SharedRWs.get("system_info")

        def update(dictionary: dict):
            dictionary["failures"] = 1 + dictionary["failures"]

        system_info.apply(update)

    @classmethod
    def get(cls):
        return SharedRWs.get("system_info").data_copy()


# BaseModel subclasses


class FilePathe(BaseModel):
    path: str


class DateTime(BaseModel):
    dt: datetime


class DateTime2(BaseModel):
    dt1: datetime
    dt2: datetime


class Http(BaseModel):
    """
    Http objects make it easier to send requests to other hosts/ports.

    Includes signatures with BaseModel as well as json string arguments.
    """

    host: str
    port: int

    def get(self, path: str, data=None):
        response = requests.get(self.cmd(path), data)
        assert response.status_code == 200, response.text
        return response.json()

    def put(self, path: str, data: BaseModel):
        response = requests.put(self.cmd(path), data.json())
        assert response.status_code == 200, response.text
        return response.json()

    def post(self, path: str, data: BaseModel):
        response = requests.post(self.cmd(path), data.json())
        assert response.status_code == 200, response.text
        return response.json()

    def patch(self, path: str, data: BaseModel):
        response = requests.post(self.cmd(path), data.json())
        assert response.status_code == 200, response.text
        return response.json()

    def put_json(self, path: str, json: str):
        response = requests.put(self.cmd(path), json)
        assert response.status_code == 200, response.text
        return response.json()

    def post_json(self, path: str, json: str):
        response = requests.post(self.cmd(path), json)
        assert response.status_code == 200, response.text
        return response.json()

    def patch_json(self, path: str, json: str):
        response = requests.post(self.cmd(path), json)
        assert response.status_code == 200, response.text
        return response.json()

    def put_dict(self, path: str, data: dict):
        response = requests.put(self.cmd(path), json.dumps(data))
        assert response.status_code == 200, response.text
        return response.json()

    def post_dict(self, path: str, data: dict):
        response = requests.post(self.cmd(path), json.dumps(data))
        assert response.status_code == 200, response.text
        return response.json()

    def patch_dict(self, path: str, data: dict):
        response = requests.post(self.cmd(path), json.dumps(data))
        assert response.status_code == 200, response.text
        return response.json()

    def delete(self, path: str):
        response = requests.delete(self.cmd(path))
        assert response.status_code == 200, response.text
        return response.json()

    def cmd(self, path: str):
        return f"http://{self.host}:{self.port}{path}"


class Rez(BaseModel):
    result: Optional[Any] = None
    flds: Optional[Dict[str, Any]] = None
    rez: Optional[
        BaseModel
    ] = None  # actually a Rez -- cannot define self-referencing classes
    extra: Optional[Dict[str, Any]] = None
    info: Optional[Dict[str, Any]] = None

    def flatten_results(self):
        results = []
        rez = self
        while rez != None:
            results.append(rez.flatten_result())
            rez = rez.rez
        return results

    def flatten_result(self):
        return {
            "action_info": self.info,
            "action_result": self.result
            if self.result != None
            else "Empty action result",
        }
