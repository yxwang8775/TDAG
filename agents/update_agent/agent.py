import json

from agents.update_agent.prompt import SYSTEM_PROMPT, USER_FIRST_PROMPT
from agents.base_agent import BaseAgent
from utils.api_service import chat_gpt
from utils.code import get_content_list
from utils.prompt import generate_prompt
import copy


class UpdateAgent(BaseAgent):
    def __init__(self, task1,solution1,task2,solution2, record_path=None, model_name='gpt-3.5-turbo-0613',
                 proxy='http://127.0.0.1:10809'):
        super().__init__(record_path, model_name, proxy)
        self.system_prompt = self.generate_system_prompt()
        self.messages.append({'role': 'system',
                              'content': self.system_prompt})
        self.solution=solution1
        self.messages.append({'role': 'user',
                              'content': self.generate_first_user_prompt(task1=task1,
                                                                         solution1=solution1,
                                                                         task2=task2,
                                                                         solution2=solution2)})


    def generate_system_prompt(self):
        system_prompt = SYSTEM_PROMPT
        replace_dict = {
        }
        return generate_prompt(template=system_prompt, replace_dict=replace_dict)

    def generate_first_user_prompt(self, task1,solution1,task2,solution2):
        user_prompt = USER_FIRST_PROMPT
        replace_dict = {
            '{{task1}}': str(task1),
            '{{solution1}}': solution1,
            '{{task2}}': str(task2),
            '{{solution2}}':solution2
        }
        return generate_prompt(template=user_prompt, replace_dict=replace_dict)

    def get_new_solution(self):
        response = chat_gpt(self.messages, model_name=self.model_name, proxy=self.proxy)
        self.messages.append(response)
        if self.record_path is not None:
            with open(self.record_path, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, indent=4, ensure_ascii=False)
        text = response['content']
        functions = self.parse_functions(text)

        if len(functions) == 0 or functions[0]['function_name'] == 'keep':
            return self.solution
        elif functions[0]['function_name'] == 'update':
            return functions[0]['args'][0]