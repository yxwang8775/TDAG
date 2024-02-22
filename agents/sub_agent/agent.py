import json

from agents.sub_agent.prompt import SYSTEM_PROMPT, MAX_ITER, CHECK_PROMPT, USER_PROMPT, USER_OVER_PROMPT \
    , USER_ERROR_PROMPT, SOLUTION_PROMPT, USER_FIRST_PROMPT
from agents.base_agent import BaseAgent

import copy
from utils.code import get_content, get_content_list
from utils.prompt import generate_prompt


class SubAgent(BaseAgent):
    def __init__(self, action, total_task, current_task, completed_task, record_path=None,
                 model_name='gpt-3.5-turbo-0613', proxy='http://127.0.0.1:10809',api_interval=20):
        super().__init__(record_path, model_name, proxy, api_interval)
        self.total_task = total_task
        self.subtasks = []
        self.completed_tasks = []

        self.system_prompt = self.generate_system_prompt(action=action, total_task=total_task,
                                                         current_task=current_task,
                                                         completed_task=completed_task)
        self.action_apace = self.get_action_space()
        self.messages.append({'role': 'system',
                              'content': self.system_prompt})
        self.messages.append({'role': 'user',
                              'content': self.generate_first_user_prompt(current_task=current_task)})

    def generate_first_user_prompt(self, current_task):
        user_prompt = USER_FIRST_PROMPT
        replace_dict = {
            '{{current_task}}': str(current_task),
            '{{action_space}}': self.get_action_space()
        }

        return generate_prompt(template=user_prompt, replace_dict=replace_dict)

    def generate_system_prompt(self, action, total_task, current_task, completed_task):
        system_prompt = SYSTEM_PROMPT
        replace_dict = {
            '{{action}}': action,
            '{{max_iter}}': str(MAX_ITER),
            '{{total_task}}': str(total_task),
            '{{current_task}}': str(current_task),
            '{{completed_task}}': str(completed_task)
        }
        return generate_prompt(template=system_prompt, replace_dict=replace_dict)

    def generate_verify_prompt(self, check_ans):
        check_prompt = CHECK_PROMPT
        replace_dict = {
            '{{answer}}': check_ans
        }
        prompt = copy.deepcopy(check_prompt)
        for k, v in replace_dict.items():
            prompt = prompt.replace(k, v)
        return prompt

    def add_user_prompt(self, observation):
        user_prompt = USER_PROMPT
        replace_dict = {
            '{{observation}}': observation,
            '{{action_space}}': str(self.action_apace)
        }
        prompt = generate_prompt(template=user_prompt, replace_dict=replace_dict)
        print(f'user prompt={prompt}')
        self.messages.append({'role': 'user', 'content': prompt})

    def add_user_error_prompt(self, observation):
        user_prompt = USER_ERROR_PROMPT
        replace_dict = {
            '{{observation}}': observation,
        }
        prompt = generate_prompt(template=user_prompt, replace_dict=replace_dict)
        print(f'user prompt={prompt}')
        self.messages.append({'role': 'user', 'content': prompt})

    def add_over_prompt(self):
        self.messages.append({'role': 'user', 'content': USER_OVER_PROMPT})

    def add_verify_prompt(self, check_ans):
        check_prompt = CHECK_PROMPT
        replace_dict = {
            '{{answer}}': check_ans
        }
        prompt = copy.deepcopy(check_prompt)
        for k, v in replace_dict.items():
            prompt = prompt.replace(k, v)
        self.messages.append({'role': 'user',
                              'content': f'{prompt}'})

    def get_result(self, text):
        return get_content(text, begin_str='<result>', end_str='</result>')

    def get_process(self, text):
        return get_content(text, begin_str='<process>', end_str='</process>')

    def load_from_json(self, json_path):
        with open(json_path, "r",encoding="utf-8") as json_file:
            self.messages = json.load(json_file)
        self.system_prompt = self.messages[0]['content']
        self.action_apace = self.get_action_space()

    def add_solution_prompt(self):
        self.messages.append({'role': 'user',
                              'content': f'{SOLUTION_PROMPT}'})
