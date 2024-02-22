from agents.verify_agent.prompt import SYSTEM_PROMPT
from agents.base_agent import BaseAgent
from utils.prompt import generate_prompt


class VerifyAgent(BaseAgent):
    def __init__(self, total_task, current_task, completed_task, process, result, record_path=None,
                 model_name='gpt-3.5-turbo-0613', proxy='http://127.0.0.1:10809'):
        super().__init__(record_path, model_name, proxy)
        self.messages.append({'role': 'system',
                              'content': self.generate_system_prompt(total_task=total_task, current_task=current_task,
                                                                     completed_task=completed_task, process=process,
                                                                     result=result)})
        self.messages.append({'role': 'user',
                              'content': 'Start.'})

    def generate_system_prompt(self, total_task, current_task, completed_task, process, result):
        system_prompt = SYSTEM_PROMPT
        replace_dict = {
            '{{total_task}}': total_task,
            '{{current_task}}': str(current_task),
            '{{completed_task}}': str(completed_task),
            '{{process}}': process,
            '{{result}}': result
        }
        return generate_prompt(template=system_prompt, replace_dict=replace_dict)
