import copy
import json
import os
import time

import openai
import requests

from agents.ps_agent.agent import PSAgent
from task.travel.simulator import TravelSimulator
from utils.code import get_content, get_content_list
from utils.config_manager import ConfigManager
from utils.travel import execute_sql, execute_python, is_error, check_plan_format
proxy = None
config_manager = ConfigManager()

model_name = 'gpt-3.5-turbo-16k'
MAX_ITER = 20
max_error_times = 3
api_interval = 10

def invoke_function(func_data):
    func = globals()[func_data['function_name']]
    result = func(*func_data['args'])
    return result


def run_item(task, output_path="."):
    plan_strs = []
    max_iter = MAX_ITER
    if type == 1:
        from agents.ps_agent.prompt import EXAMPLE_MESSAGES_1
        main_agent = PSAgent(model_name=model_name, task=task,
                             record_path=f'{output_path}/ps_agent_record.json',
                             example_message=EXAMPLE_MESSAGES_1,proxy=proxy,api_interval=api_interval)
    elif type == 2:
        from agents.ps_agent.prompt import EXAMPLE_MESSAGES_2
        main_agent = PSAgent(model_name=model_name, task=task,
                             record_path=f'{output_path}/ps_agent_record.json',
                             example_message=EXAMPLE_MESSAGES_2,proxy=proxy,api_interval=api_interval)
    else:
        from agents.ps_agent.prompt import EXAMPLE_MESSAGES_3
        main_agent = PSAgent(model_name=model_name, task=task,
                             record_path=f'{output_path}/ps_agent_record.json',
                             example_message=EXAMPLE_MESSAGES_3,proxy=proxy,api_interval=api_interval)

    cur_iter = 0
    completed = False
    try:
        error_times = 0
        while cur_iter < max_iter:
            call_over = False
            cur_iter += 1
            response = main_agent.get_response()
            text = response['content']
            functions = main_agent.parse_functions(text)
            observation = f'No valid action found.\nAvailable actions:{main_agent.get_action_space()}\nGive me the action between <action> and </action>.'
            for function in functions:
                try:
                    if function['function_name'] == 'over':
                        call_over = True
                    observation = invoke_function(function)
                    exec_function = function
                    break
                except Exception as e:
                    observation = f'{e}. No valid action found. Available actions:{main_agent.get_action_space()}\n Give me the action between <action> and </action>. Make sure to pass in the correct parameters'
                    print(e)
            if is_error(observation):
                if "is not defined" in observation:
                    observation = observation + "The interpreter does not store previous code or variables. So you should define the variable before your code."
                error_times += 1
            else:
                error_times = 0
            if error_times >= max_error_times:
                name = exec_function['function_name']
                main_agent.messages = main_agent.messages[:-((max_error_times - 1) * 2)]
                observation = f"For some unknown reason, this step cannot be completed with {name}. Try to solve this problem yourself."

            if call_over:
                completed = True
                main_agent.add_over_prompt()
                response = main_agent.get_response()
                text = response['content']
                plan_strs = get_content_list(text, begin_str='<plan>', end_str='</plan>')
                break
            print(f'observation={observation}')
            if error_times > 0:
                main_agent.add_user_error_prompt(observation)
            else:
                main_agent.add_user_prompt(observation)
        if cur_iter >= max_iter:
            main_agent.add_over_prompt()
            response = main_agent.get_response()
            text = response['content']
            plan_strs = get_content_list(text, begin_str='<plan>', end_str='</plan>')
    except openai.error.InvalidRequestError as e:
        print(f'{e} InvalidRequestError. Context length error?')
        for idx in range(len(main_agent.messages) - 1, 0, -1):
            if main_agent.messages[idx]["role"] == "user":
                break
        main_agent.messages = main_agent.messages[:idx - 2]  # 从后往前删掉idx:user, idx-1:assistant, idx-2:user
        main_agent.add_over_prompt()
        try:
            response = main_agent.get_response()
        except openai.error.InvalidRequestError as e:
            for idx in range(len(main_agent.messages) - 1, 0, -1):
                if main_agent.messages[idx]["role"] == "user":
                    break
            main_agent.messages = main_agent.messages[:idx - 2]  # 从后往前删掉idx:user, idx-1:assistant, idx-2:user
            main_agent.add_over_prompt()
            response = main_agent.get_response()
        text = response['content']
        plan_strs = get_content_list(text, begin_str='<plan>', end_str='</plan>')
    check_result = check_plan_format(text)
    if "No valid plan format found." in check_result:
        main_agent.messages.append({"role": "user", "content": f"{check_result}"})
        response = main_agent.get_response()
        print(response)
        text = response['content']
        check_result = check_plan_format(text)
    if check_result != "All formats are correct.":
        main_agent.messages.append({"role": "user", "content": f"{check_result}"})
        response = main_agent.get_response()
        print(response)
        text = response['content']
    plan_strs = get_content_list(text, begin_str='<plan>', end_str='</plan>')
    return plan_strs, completed


def run(type, begin=0, end=99, step=1):
    output_dir = f'./output/travel/ps/{model_name}/type{type}'
    data_path = f'./data/travel/data_type{type}.json'
    with open(data_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    data = data[begin:end:step]
    for data_idx, d in enumerate(data):
        print(f'data_idx={data_idx}')
        prediction = []
        # try:
        print(f'{data_idx}:{time.localtime()}')
        task_id = begin + data_idx * step
        if task_id%5 in [0,1]:
            continue
        print(f'task_id:{task_id}')
        output_path = f'{output_dir}/{task_id}'
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        prediction_file = f'{output_path}/prediction.json'
        task = d['question']
        simulator = TravelSimulator(**d['demands']['TravelSimulator'])
        simulator.create_constraints(d['demands']['Constraints'])
        plan_strs, completed = run_item(task=task, output_path=output_path)
        for plan_str in plan_strs:
            print(f'plan_str={plan_str}')
            simulator.action(plan_str)
        simulator.over()
        print(f'geterror')
        errors = simulator.get_errors()
        score = simulator.get_score()
        print(f'state={simulator.state}')
        prediction.append(
            {"question": d['question'], "plan": plan_strs, "errors": errors, "score": score,
             "over": completed, "state": str(simulator.state)})
        print(f'prediction={prediction}')
        with open(prediction_file, 'w', encoding='utf-8') as f:
            json.dump(prediction, f, indent=4, ensure_ascii=False)
        # except Exception as e:
        #     print(f'{data_idx}:{e}')


for type in [1, 2, 3]:
    if type == 1:
        run(type, begin=0, end=999, step=1)
    if type == 2:
        run(type, begin=0, end=999, step=1)
    elif type == 3:
        run(type, begin=0, end=999, step=1)
