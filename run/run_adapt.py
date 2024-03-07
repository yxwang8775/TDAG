import copy
import json
import os
import sys
import time

import openai
import requests

from agents.agent_generator.prompt import ORIGINAL_DOCUMENT
from agents.plan_and_execute.planner.agent import Planner
from agents.plan_and_execute.executor.agent import Executor
from agents.plan_and_execute.executor.prompt import fail_action
from agents.sub_agent.prompt import MAX_ITER
from agents.base_agent import BaseAgent
from task.travel.simulator import TravelSimulator
from utils.code import get_content, get_content_list
from utils.config_manager import ConfigManager
from utils.travel import execute_sql, execute_python, is_error, check_plan_format

config_manager = ConfigManager()
proxy = None
from utils.api_service import set_keys

model_name = 'gpt-3.5-turbo-16k'
type = 1
max_error_times = 3
agent_id = 0
max_depth = 3
sub_max_iter = MAX_ITER
api_interval = 5


def invoke_function(func_data):
    func = globals()[func_data['function_name']]
    result = func(*func_data['args'])
    return result


def subagent_handle2(overall_task, completed_tasks, current_task, verify=False, depth=2, output_path='.'):
    if depth > max_depth:
        return 'fail'
    print(f'\nsubagent_handle2({overall_task},{completed_tasks}, {current_task}, {verify},{depth},{output_path})\n')
    global agent_id

    executor = Executor(model_name=model_name, action=ORIGINAL_DOCUMENT + fail_action, total_task=overall_task,
                        current_task=current_task, api_interval=api_interval, proxy=proxy,
                        completed_task=completed_tasks, record_path=f'{output_path}/executor_{agent_id}.json')

    agent_id += 1
    cur_sub_iter = 0
    try:
        error_times = 0
        while cur_sub_iter < sub_max_iter:
            print(f'cur_iter={cur_sub_iter}')
            cur_sub_iter += 1
            response = executor.get_response()
            print(f'response {response}')
            text = response['content']
            # subagent.subtasks.extend(subagent.get_subtasks(text))
            functions = executor.parse_functions(text)

            print(f'functions={functions}')
            if len(functions) == 0:
                print('no action')
                executor.messages.append(
                    {'role': 'user',
                     'content': f'Available Actions:{executor.action_apace}\nGive me the action between <action> and </action>.'})
                response = executor.get_response()
                print(f'response {response}')
                text = response['content']
                # subagent.subtasks.extend(subagent.get_subtasks(text))
                functions = executor.parse_functions(text)

            observation = 'No valid action found. Surround it by <action> and </action>'
            exec_function = None
            for function in functions:
                try:
                    if function['function_name'] == 'over':
                        break
                    if function['function_name'] == 'fail':
                        return 'fail'
                    observation = invoke_function(function)
                    exec_function = function
                    break
                except Exception as e:
                    observation = f'{e}. No valid action found. Surround it by <action> and </action>. Make sure to pass in the correct parameters'
                    print(e)
            if is_error(observation):
                if "is not defined" in observation:
                    observation = observation + "The interpreter does not store previous code or variables. So you should define the variable before your code."
                error_times += 1
            else:
                error_times = 0
            if error_times >= max_error_times:
                name = exec_function['function_name']
                executor.messages = executor.messages[:-((max_error_times - 1) * 2)]
                observation = f"For some unknown reason, this step cannot be completed with {name}. Try to solve this problem yourself."

            print(f'observation {observation}')
            if len(functions) > 0 and functions[0]['function_name'] == 'over':
                executor.add_over_prompt()
                response = executor.get_response()
                print(f'response {response}')
                text = response['content']
                break
            if error_times > 0:
                executor.add_user_error_prompt(observation)
            else:
                executor.add_user_prompt(observation)
    except openai.error.InvalidRequestError as e:
        print(f'{e} InvalidRequestError. Context length error?')
        return 'fail'
    if cur_sub_iter >= sub_max_iter:
        return 'fail'
    result = executor.get_result(text)
    return result


def subagent_handle(task_name, agent: BaseAgent, output_path, depth=2):
    print(f'subagent_handle({task_name} {agent})')
    overall_task = agent.task
    completed_tasks = agent.completed_tasks
    current_task = None
    for subtask in agent.subtasks:
        if subtask['subtask_name'] == task_name:
            current_task = subtask
    if current_task is None:
        from agents.main_agent.prompt import subtask_format
        return f'''Cannot find a subtask named {task_name}.
make sure that a subtask-structure has the following json component and surrounded with <subtask></subtask> as follows:
{subtask_format}'''
    else:
        result = subagent_handle2(overall_task=overall_task, completed_tasks=completed_tasks, current_task=current_task,
                                  output_path=output_path, depth=depth)
        completed_task = copy.deepcopy(current_task)
        completed_task['result'] = result
        agent.completed_tasks.append(completed_task)
        return result


def plan_and_run(task_name, agent: BaseAgent, output_path, depth=1):
    if depth > max_depth:
        return 'fail'

    result = subagent_handle(task_name=task_name, agent=agent, output_path=output_path, depth=depth + 1)
    if 'fail' not in result:
        return result

    # If failed, decompose and recursive execution
    task = None
    for subtask in agent.subtasks:
        if subtask['subtask_name'] == task_name:
            task = subtask

    from agents.plan_and_execute.planner.prompt import EXAMPLE_MESSAGES_3
    global agent_id
    planner = Planner(model_name=model_name, task=task, api_interval=api_interval, proxy=proxy,
                      record_path=f'{output_path}/planner_record_{agent_id}.json',
                      example_message=EXAMPLE_MESSAGES_3)
    agent_id += 1

    subtasks = planner.generate_subtasks()
    for subtask in subtasks:
        plan_and_run(task_name=subtask['subtask_name'], agent=planner, output_path=output_path, depth=depth + 1)
    observation = planner.completed_tasks
    planner.add_result_prompt(observation=observation)
    response = planner.get_response()
    text = response['content']
    result = get_content(text, begin_str='<result>', end_str='</result>')
    if result != '':
        return result
    return text


def run_item(task, output_path="."):
    global agent_id
    agent_id = 0

    if type == 1:
        from agents.plan_and_execute.planner.prompt import EXAMPLE_MESSAGES
        planner = Planner(model_name=model_name, task=task,
                          record_path=f'{output_path}/planner_record.json',
                          example_message=EXAMPLE_MESSAGES)
    elif type == 2:
        from agents.plan_and_execute.planner.prompt import EXAMPLE_MESSAGES_2
        planner = Planner(model_name=model_name, task=task,
                          record_path=f'{output_path}/planner_record.json',
                          example_message=EXAMPLE_MESSAGES_2)
    else:
        from agents.plan_and_execute.planner.prompt import EXAMPLE_MESSAGES_3
        planner = Planner(model_name=model_name, task=task,
                          record_path=f'{output_path}/planner_record.json',
                          example_message=EXAMPLE_MESSAGES_3)

    subtasks = planner.generate_subtasks()
    for subtask in subtasks:
        # subagent_handle(task_name=subtask['subtask_name'], agent=planner, output_path=output_path)
        plan_and_run(task_name=subtask['subtask_name'], agent=planner, output_path=output_path, depth=2)
    observation = planner.completed_tasks

    planner.add_over_prompt(observation=observation)
    response = planner.get_response()
    text = response['content']
    # plan_strs = get_content_list(text, begin_str='<plan>', end_str='</plan>')
    check_result = check_plan_format(text)
    if "No valid plan format found." in check_result:
        planner.messages.append({"role": "user", "content": f"{check_result}"})
        response = planner.get_response()
        print(response)
        text = response['content']
        check_result = check_plan_format(text)
    if check_result != "All formats are correct.":
        planner.messages.append({"role": "user", "content": f"{check_result}"})
        response = planner.get_response()
        print(response)
        text = response['content']
    plan_strs = get_content_list(text, begin_str='<plan>', end_str='</plan>')
    return plan_strs, True


def run(type, begin=0, end=99, step=1):
    print(type, begin, end, step)
    output_dir = f'./output/travel/adapt/{model_name}/type{type}'
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
        if task_id % 10 == 0:
            continue
        print(f'task_id={task_id}')
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


for type in [1, 2, 3]:
    if type == 1:
        run(type, begin=0, end=999, step=1)
    elif type == 2:
        run(type, begin=0, end=999, step=1)
    elif type == 3:
        run(type, begin=0, end=999, step=1)
