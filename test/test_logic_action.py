import whendo.core.actions.logic_action as logic_x
from whendo.core.action import Action

def negate(action:Action):
    return logic_x.NotAction(operand_action=action)

def is_exception(result):
    return isinstance(result, Exception)

# =================== tests ==================?

def test_success_1():
    assert not is_exception(logic_x.SuccessAction().execute())

def test_exception_1():
    assert is_exception(logic_x.ExceptionAction().execute())

def test_not_1():
    
    class Action1(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            return Exception()

    action1 = Action1()
    action2 = negate(action1)
    action3 = negate(action2)
    assert is_exception(action1.execute())
    assert not is_exception(action2.execute())
    assert is_exception(action3.execute())

def test_not_2():
    
    class Action1(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            return True

    action1 = Action1()
    action2 = negate(action1)
    action3 = negate(action2)
    assert not is_exception(action1.execute())
    assert is_exception(action2.execute())
    assert not is_exception(action3.execute())

def test_list_action_all_1():
    dictionary = {'value':None}

    class Action1(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action2(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action3(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action4(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
    
    list_action = logic_x.ListAction(op_mode=logic_x.ListOpMode.ALL, action_list=[Action1(), Action2(), Action3(), Action4()])
    result = list_action.execute()
    assert result is not None
    assert not is_exception(result)
    assert dictionary['value'] == Action4

def test_list_action_or_1():
    dictionary = {'value':None}

    class Action1(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action2(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action3(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action4(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__

    list_action = logic_x.ListAction(op_mode=logic_x.ListOpMode.OR, action_list=[negate(Action1()), Action2(), Action3(), Action4()])
    result = list_action.execute()
    assert result is not None
    assert not is_exception(result)
    assert dictionary['value'] == Action2

def test_list_action_and_1():
    dictionary = {'value':None}

    class Action1(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action2(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action3(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action4(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__

    list_action = logic_x.ListAction(op_mode=logic_x.ListOpMode.AND, action_list=[Action1(), Action2(), Action3(), Action4()])
    result = list_action.execute()
    assert result is not None
    assert not is_exception(result)
    assert dictionary['value'] == Action4

def test_list_action_and_2():
    dictionary = {'value':None}

    class Action1(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action2(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action3(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
        
    class Action4(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__

    list_action = logic_x.ListAction(op_mode=logic_x.ListOpMode.AND, action_list=[negate(Action1()), negate(Action2()), negate(Action3()), negate(Action4())])
    result = list_action.execute()
    assert result is not None
    assert not is_exception(result)
    assert dictionary['value'] == Action1

def test_list_action_and_3():
    dictionary = {'value':None}

    class Action1(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            return Exception()
        
    class Action2(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            return Exception()
        
    class Action3(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            return Exception()
        
    class Action4(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            return Exception()

    list_action = logic_x.ListAction(
        op_mode=logic_x.ListOpMode.AND,
        action_list=[Action1(), Action2(), Action3(), Action4()],
        exception_on_no_success=True
        )
    result = list_action.execute()
    assert result is not None
    assert is_exception(result)

def test_if_else_action_and_1():
    dictionary = {'value':None}

    class Action1(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True
        
    class Action2(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True
        
    class Action3(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True
        
    class Action4(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True

    list_action = logic_x.IfElseAction(
        op_mode=logic_x.ListOpMode.AND,
        test_action=Action1(),
        else_action=Action2(),
        if_actions=[Action3(), Action4()],
        exception_on_no_success=False
        )
    result = list_action.execute()
    assert result is not None
    assert not is_exception(result)
    assert dictionary['value'] == Action4

def test_if_else_action_or_2():
    dictionary = {'value':None}

    class Action1(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True
        
    class Action2(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True
        
    class Action3(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True
        
    class Action4(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True

    list_action = logic_x.IfElseAction(
        op_mode=logic_x.ListOpMode.OR,
        test_action=Action1(),
        else_action=Action2(),
        if_actions=[Action3(), Action4()],
        exception_on_no_success=False
        )
    result = list_action.execute()
    assert result is not None
    assert not is_exception(result)
    assert dictionary['value'] == Action3

def test_if_else_action_else_1():
    dictionary = {'value':None}

    class Action1(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            return Exception()
        
    class Action2(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True
        
    class Action3(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True
        
    class Action4(Action):
        def execute(self, tag:str=None, scheduler_info:dict=None):
            dictionary['value'] = self.__class__
            return True

    list_action = logic_x.IfElseAction(
        op_mode=logic_x.ListOpMode.OR,
        test_action=Action1(),
        else_action=Action2(),
        if_actions=[Action3(), Action4()],
        exception_on_no_success=False
        )
    result = list_action.execute()
    assert result is not None
    assert not is_exception(result)
    assert dictionary['value'] == Action2