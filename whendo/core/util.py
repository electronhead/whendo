from enum import Enum
from pprint import PrettyPrinter
from sys import stdout
# import netifaces
from datetime import datetime
from typing import Callable
import os
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
from threading import RLock

# Enums

class HttpVerb(str, Enum):
    """
    usage:
        HttpVerb.get
    """
    get = 'get'
    put = 'put'
    patch = 'patch'
    post = 'post'
    delete = 'delete'

class TimeUnit(str, Enum):
    """
    usage:
        TimeUnit.minute
    """
    day = 'day'
    hour = 'hour'
    minute = 'minute'
    second = 'second'

# functions

def all_visible_subclasses(klass):
    def helper(klas, result):
        subklases = klas.__subclasses__()
        if len(subklases) > 0:
            result.update(subklases)
            for subklas in subklases:
                helper(subklas, result)
    result = set()
    helper(klass, result)
    return result

def key_strings_from_dict(dictionary:Dict[str, Any]):
    return set(x for x in dictionary)

def key_strings_from_class(klass):
    return set(x for x in klass.__fields__.keys())

def find_class(klass, dictionary:Dict[str, Any]):
    dictionary_keys = key_strings_from_dict(dictionary)
    classes = all_visible_subclasses(klass)
    classes.add(klass) # the top class might not be abstract
    min_count = 100
    found_class = None
    for clas in classes:
        class_keys = key_strings_from_class(clas)
        if len(dictionary_keys - class_keys) == 0: # make sure class has enough fields
            count = len(class_keys)
            if count<min_count: # pick class with fewest fields, resulting in tightest conformance with dictionary
                found_class = clas
                min_count = count
    return found_class

def resolve_instance(klass, dictionary:Dict[str, Any], check_for_found_class:bool=True):
    """
    if an (improper) subclass is found that maps to the supplied dictionary, the dictionary
    is converted to an instance of that class. If the dictionary contains lists of dictionaries,
    those dictionaries are recursively resolved.
    """
    found_class = find_class(klass, dictionary)
    if found_class is None:
        if check_for_found_class:
            raise NameError(f"could not resolve dictionary ({dictionary}) to a subclass of ({klass})")
        else:
            return dictionary
    else:
        # resolve singleton dictionary elements; not constrained to producing instance of klass subclass
        for (key, value) in dictionary.items():
            if isinstance(value, dict):
                dictionary[key] = resolve_instance(klass, dictionary=value, check_for_found_class=False)
        # resolve list containing all dictionary elements; likelihood of non-klass in this circumstance
        # is very small, therefore more strict than for singletons
        for (key, value) in dictionary.items():
            if isinstance(value, list):
                if all(isinstance(element, dict) for element in value):
                    dictionary[key] = list(resolve_instance(klass, dictionary=element) for element in value)
        return found_class(**dictionary)

def object_info(obj):
    return {
        'class': f"{obj.__class__.__module__}.{obj.__class__.__name__}",
        'instance': obj
    }

# classes

class Now:
    @classmethod
    def s(cls):
        now = cls.dt()
        return f"{now.strftime('%H:%M:%S')} on {now.strftime('%Y-%m-%d')}"
    @classmethod
    def dt(cls):
        return datetime.now()
    @classmethod
    def t(cls):
        return cls.dt().time()

class Output:
    """
    usage:
    Output.pprint(dictionary={'a', 'abc'}, lev_fil=('debug', Output.debug()))
    """
    @classmethod
    def debug(cls):
        return 'debug', Dirs.output_dir() + 'output.txt'

    @classmethod
    def pprint(cls, lev_fil:tuple[str,str], dictionary:dict):
        level, file = lev_fil
        something = {'level':level}
        something.update(dictionary)
        with open(file, 'a') as outfile:
            PP.pprint(something, stream=outfile)

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

class IP:
    """
    usage:
        IP.addr
    note:
        singleton
    lineage:
        from netifaces import interfaces, ifaddresses, AF_INET
        for ifaceName in interfaces():
            addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
            print ('%s: %s' % (ifaceName, ', '.join(addresses)))
    """
    local = '127.0.0.1'
    addr = "need a fix for linux"#netifaces.ifaddresses('en0').setdefault(netifaces.AF_INET)[0]['addr']
    @classmethod
    def reset(cls):
        cls.addr = "need a fix for linux"#netifaces.ifaddresses('en0').setdefault(AF_INET)[0]['addr']


class Dirs:
    """
    This class computes directory paths for saved, output and log files. It creates the directories if absent.
    """
    @classmethod
    def saved_dir(cls, root_path:Path=None):
        return cls.assure_dir(cls.compute_dir(label='saved', root_path=root_path))
    @classmethod
    def output_dir(cls, root_path:Path=None):
        return cls.assure_dir(cls.compute_dir(label='output', root_path=root_path))
    @classmethod
    def log_dir(cls, root_path:Path=None):
        return cls.assure_dir(cls.compute_dir(label='log', root_path=root_path))

    @classmethod
    def compute_dir(cls, label:str, root_path:Path=None):
        path = root_path if root_path else Path.home()
        return str(path / f".whendo/{label}") + '/'
    @classmethod
    def assure_dir(cls, assured_dir:str):
        if not os.path.exists(assured_dir):
            os.makedirs(assured_dir)
        return assured_dir

class FilePathe(BaseModel):
    path: str

class SharedRO():
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
    def __init__(self, dictionary:dict={}):
        self.data = dictionary.copy()

    def data_copy(self):
        return self.data.copy()

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
    def __init__(self, dictionary:dict={}):
        super().__init__(dictionary=dictionary)
        self.lock = RLock()
    
    def apply(self, callable:Callable):
        """
        Transactionally applies callable to a copy of the data. A failure within
        the callable won't corrupt the dictionary.
        """
        with self.lock:
            copy = self.data_copy()
            result = callable(copy)
            self.data = copy
            return result

class SharedROs:
    """
    A dictionary of instances of SharedRO's.
    """
    singletons:Dict[str, SharedRO] = {}

    @classmethod
    def get(cls, label:str, dictionary:dict) -> SharedRO:
        if label not in cls.singletons:
            cls.singletons[label] = SharedRO(dictionary=dictionary)
        return cls.singletons[label]
    
    @classmethod
    def key_set(cls):
        return set(cls.singletons.keys())

class SharedRWs:
    """
    A dictionary of instances of SharedWR's.
    """
    singletons:Dict[str, SharedRW] = {}

    @classmethod
    def get(cls, label:str, dictionary:dict={}) -> SharedRW:
        if label not in cls.singletons:
            cls.singletons[label] = SharedRW(dictionary=dictionary)
        return cls.singletons[label]
    
    @classmethod
    def key_set(cls):
        return set(cls.singletons.keys())