import json
import re
from collections import defaultdict

from utils.api_service import chat_gpt


class BaseAgent:
    def __init__(self, record_path=None, model_name='gpt-3.5-turbo-0613', proxy='http://127.0.0.1:10809', api_interval=20):
        self.completed_tasks = []
        self.task = None
        self.system_prompt = None
        self.messages = []
        self.subtasks = []
        self.model_name = model_name
        self.proxy = proxy
        self.api_interval=api_interval
        self.record_path = record_path
        self.max_duplicate_times = 2

    def parse_functions(self, text):
        def extract_functions(text: str, begin="<action>", end='</action>') -> list:
            actions = re.findall(f"{re.escape(begin)}(.*?){re.escape(end)}", text, re.DOTALL)

            result = []
            for action in actions:
                match = re.match(r"(\w+)\((.*?)\)$", action.strip(), re.DOTALL)
                if match:
                    function_name, args = match.groups()
                    args = args.strip()
                    if args:
                        multi_line_str_match = re.match(r"(['\"]{3})(.*?)\1", args, re.DOTALL)
                        if multi_line_str_match:
                            args = [multi_line_str_match.group(2)]
                        else:
                            args = [arg.strip().strip('"').strip("'") for arg in args.split(',')]
                    else:
                        args = []

                    result.append({
                        "function_name": function_name,
                        "args": args
                    })

            return result

        functions = extract_functions(text=text)
        return functions

    def get_action_space(self):
        action_pattern = re.compile(r'<action>(.*?)\((.*?)\)</action>')
        actions = action_pattern.findall(self.system_prompt)

        action_dict = defaultdict(list)

        for action_name, params in actions:
            params_list = params.split(',') if params else []
            params_list = [param.strip() for param in params_list]
            if len(params_list) > len(action_dict[action_name]):
                action_dict[action_name] = params_list

        result = []
        for action_name, params in action_dict.items():
            if params:
                action_str = f'<action>{action_name}({", ".join(params)})</action>'
            else:
                action_str = f'<action>{action_name}()</action>'
            result.append(action_str)

        return result

    def get_subtasks(self, text):
        pattern = r'<subtask>(.*?)<\/subtask>'
        matches = re.findall(pattern, text, re.DOTALL)
        subtasks = []
        for match in matches:
            try:
                subtask_data = json.loads(match)
            except:
                subtask_data = {"subtask_name":match, "goal":match}
            subtasks.append(subtask_data)
        return subtasks

    def get_subtask_idx(self, subtask_name):
        for i, subtask in enumerate(self.subtasks):
            if subtask["subtask_name"] == subtask_name:
                return i
        return -1

    def add_subtask(self, subtasks):
        for subtask in subtasks:
            idx = self.get_subtask_idx(subtask['subtask_name'])
            if idx >= 0:
                self.subtasks[idx] = subtask
            else:
                self.subtasks.append(subtask)

    def add_user_prompt(self, observation):
        self.messages.append({'role': 'user', 'content': f'{observation}'})

    def add_user_error_prompt(self, observation):
        self.add_user_prompt(observation)

    def get_response(self):
        if self.check_duplicate() or len(self.messages[-1]['content'])>100000:
            response = {"role": "assistant", "content":"<action>over()</action>"}
            self.messages = self.messages[:-2 * self.max_duplicate_times]
        else:
            response = chat_gpt(messages=self.messages, model_name=self.model_name, proxy=self.proxy, sleep_time=self.api_interval)
        self.messages.append(response)
        if self.record_path is not None:
            with open(self.record_path, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, indent=4, ensure_ascii=False)
        subtasks = self.get_subtasks(response['content'])
        self.add_subtask(subtasks)
        return response

    def check_duplicate(self):
        if len(self.messages) <= 2 * self.max_duplicate_times:
            return False
        check_messages = [message['content'] for message in self.messages[-2:-2 - 2 * self.max_duplicate_times:-2]]
        all_equal = all(s == check_messages[0] for s in check_messages)
        return all_equal

    def load_from_json(self, json_path):
        with open(json_path, "r",encoding="utf-8") as json_file:
            self.messages = json.load(json_file)
