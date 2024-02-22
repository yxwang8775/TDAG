import json

from agents.agent_generator.prompt import SYSTEM_PROMPT, TOTAL_TASK, CURRENT_TASK, COMPLETED_TASK, ORIGINAL_DOCUMENT, \
    USER_FIRST_PROMPT, EXAMPLE_MESSAGES
from agents.base_agent import BaseAgent
from utils.api_service import chat_gpt
from utils.code import get_content_list
from utils.prompt import generate_prompt
import copy


class AgentGenerator(BaseAgent):
    def __init__(self, total_task, current_task, completed_task, record_path=None, model_name='gpt-3.5-turbo-0613',
                 proxy='http://127.0.0.1:10809'):
        super().__init__(record_path, model_name, proxy)
        self.system_prompt = self.generate_system_prompt()
        self.messages.append({'role': 'system',
                              'content': self.system_prompt})
        self.messages.extend(EXAMPLE_MESSAGES)
        self.messages.append({'role': 'user',
                              'content': self.generate_first_user_prompt(total_task=total_task,
                                                                         current_task=current_task,
                                                                         completed_task=completed_task)})


    def generate_system_prompt(self):
        system_prompt = SYSTEM_PROMPT
        replace_dict = {
            # '{{total_task}}': str(total_task),
            # '{{current_task}}': str(current_task),
            # '{{completed_task}}': str(completed_task)
        }
        return generate_prompt(template=system_prompt, replace_dict=replace_dict)

    def generate_first_user_prompt(self, total_task, current_task, completed_task):
        user_prompt = USER_FIRST_PROMPT
        replace_dict = {
            '{{total_task}}': total_task,
            '{{current_task}}': current_task,
            '{{completed_task}}': completed_task
        }
        return generate_prompt(template=user_prompt, replace_dict=replace_dict)

    def generate_agent_prompt(self, generate=False):
        if not generate:
            return ORIGINAL_DOCUMENT
        else:
            response = chat_gpt(self.messages, model_name=self.model_name, proxy=self.proxy)
            self.messages.append(response)
            if self.record_path is not None:
                with open(self.record_path, 'w', encoding='utf-8') as f:
                    json.dump(self.messages, f, indent=4, ensure_ascii=False)
            new_prompts = get_content_list(response['content'], begin_str='<action document>', end_str='</action document>')
            if len(new_prompts) == 0:
                return ORIGINAL_DOCUMENT
            return new_prompts[0]
