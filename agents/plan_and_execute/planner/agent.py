from agents.plan_and_execute.planner.prompt import SYSTEM_PROMPT, USER_FIRST, USER_OVER_PROMPT, EXAMPLE_MESSAGES
from agents.base_agent import BaseAgent
from utils.prompt import generate_prompt


class Planner(BaseAgent):
    def __init__(self, task, record_path=None, model_name='gpt-3.5-turbo-0613', proxy='http://127.0.0.1:10809',example_message=EXAMPLE_MESSAGES, api_interval=20):
        super().__init__(record_path=record_path, model_name=model_name, proxy=proxy,api_interval=api_interval)
        self.task = task
        self.subtasks = []
        self.completed_tasks = []
        self.system_prompt = self.generate_system_prompt()
        self.messages.append({'role': 'system',
                              'content': self.system_prompt})
        self.action_apace = self.get_action_space()
        self.messages.extend(example_message)
        self.messages.append({'role': 'user',
                              'content': self.generate_first_user_prompt(task=self.task)})

    def generate_system_prompt(self):
        system_prompt = SYSTEM_PROMPT
        replace_dict = {
        }
        return generate_prompt(template=system_prompt, replace_dict=replace_dict)

    def generate_first_user_prompt(self, task):
        user_prompt = USER_FIRST
        replace_dict = {
            '{{task}}': str(task)
        }
        return generate_prompt(template=user_prompt, replace_dict=replace_dict)

    def add_over_prompt(self, observation):
        user_prompt = USER_OVER_PROMPT
        replace_dict = {
            '{{observation}}': observation
        }
        prompt = generate_prompt(template=user_prompt, replace_dict=replace_dict)
        self.messages.append({'role': 'user', 'content': prompt})

    def add_result_prompt(self, observation):
        user_prompt = USER_OVER_PROMPT
        replace_dict = {
            '{{observation}}': observation,
            '{{task}}': str(self.task)
        }
        prompt = generate_prompt(template=user_prompt, replace_dict=replace_dict)
        self.messages.append({'role': 'user', 'content': prompt})

    def generate_subtasks(self):
        self.get_response()
        return self.subtasks
