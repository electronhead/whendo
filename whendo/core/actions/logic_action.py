from whendo.core.action import Action
from whendo.core.resolver import resolve_action
from typing import List
from enum import Enum
import json

class NotAction(Action):
    operand_action:Action
    
    @classmethod
    def resolve(cls, dictionary:dict):
        result = cls(**dictionary)

        result.operand_action = resolve_action(result.operand_action)
        
        return result

    def execute(self, tag:str=None, scheduler_info:dict=None):
        operand_result = self.operand_action.execute(tag=tag, scheduler_info=scheduler_info)
        if isinstance(operand_result, Exception):
            return {
                'outcome':'exception negated; action execution treated as a success',
                'exception':str(operand_result),
                'action':self.info()
                }
        else:
            return Exception(
                'exception generated; action execution treaded as a failure',
                json.dumps(self.info())
            )

class ListOpMode(str, Enum):
    ALL = 'all'
    OR = 'or'
    AND = 'and'

class ListAction(Action):
    op_mode:ListOpMode
    action_list:List[Action]
    exception_on_no_success:bool=False

    @classmethod
    def resolve(cls, dictionary:dict):
        result = cls(**dictionary)

        action_list = dictionary['action_list']
        computed_action_list = [resolve_action(action_dictionary) for action_dictionary in action_list]
        result.action_list = computed_action_list

        return result

    def execute(self, tag:str=None, scheduler_info:dict=None):
        processing_count, success_count, failure_count, successful_actions, exception_actions = process_action_list(
            tag=tag,
            scheduler_info=scheduler_info,
            op_mode=self.op_mode,
            action_list=self.action_list,
            successful_actions=[],
            exception_actions=[]
            )
        processing_info = {
            'processing_count':processing_count,
            'success_count':success_count,
            'exception_count':failure_count,
            'successful_actions':successful_actions,
            'exception_actions':exception_actions
        }
        if success_count == 0 and self.exception_on_no_success:
            return Exception(
                'exception generated; action execution treated as a failure',
                json.dumps(self.dict()),
                json.dumps(processing_info)
            )
        else:
            return {'outcome':'list action executed', 'action':self.info(), 'processing_info':processing_info}

class IfElseAction(Action):
    op_mode:ListOpMode
    test_action:Action
    if_actions:List[Action]
    else_action:Action
    exception_on_no_success:bool=False

    @classmethod
    def resolve(cls, dictionary:dict):
        result = cls(**dictionary)

        result.test_action = resolve_action(result.test_action)
        result.else_action = resolve_action(result.else_action)
        action_list = dictionary['action_list']
        computed_action_list = [resolve_action(action_dictionary) for action_dictionary in action_list]
        result.action_list = computed_action_list
        
        return result

    def execute(self, tag:str=None, scheduler_info:dict=None):
        test_result = self.test_action.execute(tag=tag, scheduler_info=scheduler_info)
        processing_count = 1
        success_count = 0
        exception_count = 0
        successful_actions = []
        exception_actions = []
        else_test = isinstance(test_result, Exception)
        if else_test: # execute the else action
            exception_count = 1
            exception_actions.append(self.test_action.dict())

            else_result = else_action.execute(tag=tag, scheduler_info=scheduler_info)
            processing_count += 1
            if isinstance(else_result, Exception):
                exception_count += 1
                exception_actions.append(self.else_action.dict())
            else:
                success_count += 1
                successful_actions.append(self.else_action.dict())
        else:
            success_count += 1
            successful_actions.append(self.test_action.dict())
            processing_count, success_count, failure_count, successful_actions, exception_actions = process_action_list(
                tag=tag,
                scheduler_info=scheduler_info,
                op_mode=self.op_mode,
                action_list=self.if_actions,
                processing_count=processing_count,
                success_count=success_count,
                exception_count=exception_count,
                successful_actions=successful_actions,
                exception_actions=exception_actions
            )
        processing_info = {
            'else_test':else_test,
            'processing_count':processing_count,
            'success_count':success_count,
            'exception_count':failure_count,
            'successful_actions':successful_actions,
            'exception_actions':exception_actions
        }
        if success_count == 0 and self.exception_on_no_success:
            return Exception(
                'exception generated; action execution treated as a failure',
                json.dumps(self.dict()),
                json.dumps(processing_info)
            )
        else:
            return {'outcome':'if else action executed', 'action':self.info(), 'processing_info':processing_info}

def process_action_list(
    tag:str,
    scheduler_info:dict,
    op_mode:ListOpMode,
    action_list:List[Action],
    processing_count:int=0,
    success_count:int=0,
    exception_count:int=0,
    successful_actions:List[Action]=[],
    exception_actions:List[Action]=[]
    ):
    for action in action_list:
        result = action.execute(tag=tag, scheduler_info=scheduler_info)
        processing_count += 1
        if isinstance(result, Exception):
            exception_count += 1
            exception_actions.append(action.dict())
            if op_mode == ListOpMode.AND: # stop after first failure
                break
        else:
            success_count += 1
            successful_actions.append(action.dict())
            if op_mode == ListOpMode.OR: # stop after first success
                break
    return (processing_count, success_count, exception_count, successful_actions, exception_actions)
