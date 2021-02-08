from enum import Enum
from pprint import PrettyPrinter
from sys import stdout
import netifaces
from datetime import datetime
from typing import Union
from functools import reduce
import os
from pydantic import BaseModel
from typing import List
from pathlib import Path

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

def key_strings_from_class(klass):
    return set(x for x in klass.__fields__.keys())

def key_strings_from_dict(dictionary:dict):
    return set(x for x in dictionary)

def resolve_instance(klass, dictionary:dict):
    dictionary_keys = key_strings_from_dict(dictionary)
    classes = all_visible_subclasses(klass)
    classes.add(klass) # the top class might not be abstract
    min_count = 100
    selected_class = None
    for clas in classes:
        class_keys = key_strings_from_class(clas)
        if len(dictionary_keys - class_keys) == 0: # make sure class has enough fields
            count = len(class_keys)
            if count<min_count: # pick class with fewest fields, resulting in tightest conformance with dictionary
                selected_class = clas
                min_count = count
    return selected_class(**dictionary) if selected_class else None

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
    This class determines saved and output directories from environment variables, and if not there, will
    use the specified defaults and set the corresponding environment variables.

    If paths do not exist, this class will attempt to create the implied directory structure. Unless another
    idea presents itself, it's probably best to leave the defaults as is, keeping the directories and
    files in the installer's home directory. Can tackle file permissions for root-based directories later (/usr,
    /var, etc.).
    """
    output_label, output_default_dir = 'PYRAMBIUM_OUTPUT_DIR', str(Path.home() / 'pyrambium/output') + '/'
    saved_label, saved_default_dir = 'PYRAMBIUM_SAVED_DIR', str(Path.home() / 'pyrambium/saved') + '/'
    @classmethod
    def compute_dir(cls, label, default_dir):
        dir = os.getenv(label)
        if not dir:
            dir = default_dir
            os.environ[label] = dir # setting the environment variable is somewhat opinioated.
        if not os.path.exists(dir):
            os.makedirs(dir) # creating directories if absent is also somewhat opinionated. Opting for ease of use.
        return dir
    @classmethod
    def output_dir(cls):
        return cls.compute_dir(cls.output_label, cls.output_default_dir)
    @classmethod
    def saved_dir(cls):
        return cls.compute_dir(cls.saved_label, cls.saved_default_dir)

class FilePathe(BaseModel):
    path: str