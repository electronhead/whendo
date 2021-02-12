from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List
from whendo.core.util import Now, all_visible_subclasses, key_strings_from_class, key_strings_from_dict, FilePathe, resolve_instance

def test_now_1():
    now1 = datetime.now()
    now2 = Now.dt()
    elapsed = now2 - now1
    assert elapsed < timedelta(microseconds=100.0)

def test_now_2():
    now = datetime.now()
    now2 = Now.t()
    date2 = datetime(year=now.year, month=now.month, day=now.day, hour=now2.hour, minute=now2.minute, second=now2.second, microsecond=now2.microsecond)
    elapsed = date2 - now
    assert elapsed < timedelta(microseconds=100.0)

def test_now_3():
    now1 = datetime.now().time()
    now1_str = now1.strftime('%H:%M:%S')
    now2 = Now.s()
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
    x = all_visible_subclasses(A)
    y = {B,C,D}
    assert x == y

def test_key_strings_from_class():
    class A(BaseModel):
        a:str
        b:str
    x = {'a', 'b'}
    y = key_strings_from_class(A)
    assert x == y

def test_key_strings_from_dict():
    x = {'a', 'b'}
    y = key_strings_from_dict({'a':1, 'b':2})
    assert x == y

def test_resolve_instance():
    """
    Top > A, B, D
    D > C
    """
    class Top(BaseModel):
        pass
    class C(Top):
        c:str
    class D(C):
        d:str
        d_instance:Top
    class B(Top):
        b_instance:Top
        b_list:List[Top]
    class A(Top):
        a_list:List[Top]

    dictionary0 = {'c':'why'}
    dictionary1 = { # D
                        'c':'dc',
                        'd':'abc',
                        'd_instance': { # C
                            'c':'mmm',
                        }
                    }
    dictionary2 = { # A
        'a_list': [
            { # B
                'b_instance': { # C
                    'c':'xxx'
                    },
                'b_list': [
                    {'c':'yyy'}, # C
                    {'c':'zzz'}, # C
                    dictionary1
                    ]
            },
            { # D
                'c':'people',
                'd':'who',
                'd_instance': dictionary0
            }
        ]
    }
    instance0 = resolve_instance(Top, dictionary0)
    instance1 = resolve_instance(Top, dictionary1)
    instance2 = resolve_instance(Top, dictionary2)
    assert isinstance(instance0, C)
    assert isinstance(instance1, D)
    assert isinstance(instance2, A)
    assert isinstance(instance2.a_list[0].b_instance, C)
    assert instance1 == instance2.a_list[0].b_list[2]
    assert instance0 == instance2.a_list[1].d_instance

def test_filepathe():
    path = FilePathe(path = 'a/b/c')
    new_path = FilePathe(**(path.dict()))
    assert path.path == new_path.path, 'path reconstruction failed'