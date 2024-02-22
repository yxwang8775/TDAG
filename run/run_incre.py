import copy
import json
import os
import sys
import time

import openai
from agents.main_agent.agent import MainAgent
from agents.agent_generator.agent import AgentGenerator
from agents.sub_agent.agent import SubAgent
from agents.sub_agent.prompt import MAX_ITER
from task.travel.simulator import TravelSimulator
from utils.config_manager import ConfigManager
from utils.retrieve import get_prompt
from utils.code import get_content_list
from utils.file import get_json_refined
from utils.retrieve import get_prompt, get_similarity
from agents.verify_agent.agent import VerifyAgent
from agents.update_agent.agent import UpdateAgent

config_manager = ConfigManager()
os.environ['OPENAI_API_KEY'] = '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'
proxy = 'http://127.0.0.1:10809'
# proxy = None
from utils.api_service import set_keys

max_error_times = 3
max_depth = 2
model_name = 'gpt-3.5-turbo-16k'
agent_id = 1
sub_max_iter = MAX_ITER
method = "decompose/incre"
library_path = './data/travel/skill.json'
interrupt = 0
api_interval = 7
theta = 0.7
use_detail = False
output = open('run_incre.txt', 'w')
sys.stdout = output
extend = True
extend_ends = [32, 32, 57]

from utils.travel import query_database, execute_sql, execute_python, is_error, check_plan_format

with open(library_path, 'r', encoding='utf-8') as f:
    skills_save = list(json.load(f))

skills = copy.deepcopy(skills_save)


def check_item(agent_file):
    with open(agent_file, 'r', encoding='utf-8') as f:
        messages = list(json.load(f))
    task_message = messages[0]['content']
    result_message = messages[-1]['content']
    current_tasks = get_content_list(task_message, begin_str='And the subtask you need to complete is:',
                                     end_str='\n\n\n')
    overall_tasks = get_content_list(task_message, begin_str='The total task is: \n',
                                     end_str='\n\n')
    completed_taskss = get_content_list(task_message, begin_str='The part that has been completed is \n',
                                        end_str='\n\n')
    results = get_content_list(result_message, begin_str='<result>',
                               end_str='</result>')
    processes = get_content_list(result_message, begin_str='process>',
                                 end_str='</process>')
    if not (len(current_tasks) > 0 and len(overall_tasks) > 0 and len(completed_taskss) > 0 and len(
            results) > 0 and len(processes) > 0):
        print(f'content not found in {agent_file}')
        print(
            f'{[len(current_tasks) > 0, len(overall_tasks) > 0, len(completed_taskss) > 0, len(results) > 0, len(processes) > 0]}')
        return False

    current_task = current_tasks[0]
    overall_task = overall_tasks[0]
    completed_tasks = completed_taskss[0]
    result = results[0]
    process = processes[0]

    verify_agent = VerifyAgent(model_name=model_name, total_task=overall_task,
                               current_task=current_task,
                               completed_task=completed_tasks,
                               process=process, result=result, record_path=f'{agent_file[:-5]}_verify.json')
    response = verify_agent.get_response()
    text = response['content']
    functions = verify_agent.parse_functions(text)
    if len(functions) == 0 or functions[0]['function_name'] == 'success':
        print(f'{agent_file} success')
        return True
    elif functions[0]['function_name'] == 'fail':
        print(f'{agent_file} fail')
        return False
    return False


def generate_solution(agent_file, output_file):
    subagent = SubAgent(action="", total_task="", current_task="", completed_task="", record_path=output_file,
                        model_name=model_name)
    subagent.load_from_json(agent_file)
    subagent.add_solution_prompt()
    text = subagent.get_response()['content']
    return text


def extend_skill(agent_file, theta=0.7, max_similar_count=2):
    global interrupt
    if interrupt > 0:
        interrupt -= 1
        return

    if os.path.exists(agent_file):
        print(f'extend kill in {agent_file}')
        with open(agent_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        task_message = data[0]['content']
        sub_tasks = get_content_list(task_message, begin_str='And the subtask you need to complete is:',
                                     end_str='\n\n\n')
        result_message = data[-1]['content']
        processes = get_content_list(result_message, begin_str='<process>', end_str='</process>')
        if len(sub_tasks) > 0 and len(processes) > 0:
            try:
                global skills

                sub_task = get_json_refined(sub_tasks[0])

                task_detail = {'subtask_name': sub_task['subtask_name'], 'goal': sub_task['goal']}
                if 'result_format' in sub_task:
                    task_detail['result_format'] = sub_task['result_format']
                task_name = sub_task['subtask_name']
                similar_count = 0
                for idx_e, existing_skill in enumerate(skills):
                    if get_similarity(existing_skill['task_name'], task_name) > theta:
                        print(f"sim>{theta}\n{existing_skill['task_name']}\n{task_name}")
                        similar_count += 1
                        if similar_count >= max_similar_count:
                            break
                print(f"{sub_task['subtask_name']}:sim_count={similar_count}")

                if not check_item(agent_file=agent_file):
                    return

                solution_text = generate_solution(agent_file=agent_file, output_file=agent_file[:-5] + "_sol.json")
                solutions = get_content_list(solution_text, begin_str='<solution>', end_str='</solution>')
                if len(solutions) == 0:
                    print("solution not found")
                    return
                solution = solutions[0]

                if similar_count >= max_similar_count:
                    update_agent = UpdateAgent(task1=existing_skill['task_detail'],
                                               solution1=existing_skill['solution'],
                                               task2=task_detail,
                                               solution2=solution,
                                               record_path=f'{agent_file[:-5]}_update.json')
                    new_solution = update_agent.get_new_solution()
                    # update
                    if skills[idx_e]['solution'] != new_solution:
                        print(f"update {skills[idx_e]}: {new_solution}")
                    skills[idx_e]['solution'] = new_solution
                else:
                    skills.append(
                        {'task_name': sub_task['subtask_name'], 'task_detail': str(task_detail),
                         'solution': solution})
                    print(f"add: {skills[-1]}")
            except Exception as e:
                print("exception", e)


def over():
    summary_prompt = '''Please express the part of the plan that has been confirmed in chronological order in the following formats:
    1.go_to_place(origin:str,destination:str,departure_time,arrival_time): go to destination from origin.
    2.visit(place:str,begin_time,end_time): visit somewhere from begin_time to end_time. The time should be expressed\
     as "%Y-%m-%d %H:%M", e.g. 2023-07-02 16:00.
    3.go_to_city(origin_city:str,destination_city:str,departure_time,arrival_time,ticket_number): go to destination city from origin city, using the ticket with the ticket_number(you have known the ticket number from the database).
    4.stay_in(city:str,begin_time,end_time): stay in somewhere from begin_time to end_time. The time should be expressed\
     as "%Y-%m-%d %H:%M".
    You should surround the action between <plan> and </plan> such as <plan>go_to_place(\"Beijing Railway Hotel\",\"The Great Wall\",\
    \"2023-07-02 7:00\",\"2023-07-02 8:05\")</plan>, <plan>visit(\"Great Wall\",\
    \"2023-07-02 8:05\",\"2023-07-05 17:00\")</plan>,<plan>go_to_city(\"Shanghai\",\"Beijing\",\
    \"2023-07-02 16:00\",\"2023-07-02 22:30\",\"D1111\")</plan>, <plan>stay_in(\"Beijing\",\
    \"2023-07-02 22:30\",\"2023-07-05 8:00\")</plan>
    '''
    return summary_prompt


def invoke_function(func_data):
    func = globals()[func_data['function_name']]
    result = func(*func_data['args'])
    return result


def subagent_handle2(overall_task, completed_tasks, current_task, verify=False, depth=1, output_path='.'):
    if depth > max_depth:
        return 'Cannot decompose anymore'

    print(f'\nsubagent_handle2({overall_task},{completed_tasks}, {current_task}, {verify},{depth},{output_path})\n')
    global agent_id
    agent_generator = AgentGenerator(model_name=model_name, total_task=overall_task, completed_task=completed_tasks,
                                     current_task=current_task,
                                     record_path=f'{output_path}/agent_generator_{agent_id}.json')
    modified_prompt = agent_generator.generate_agent_prompt(generate=True)

    subagent_file = f'{output_path}/sub_agent_{agent_id}.json'
    subagent = SubAgent(model_name=model_name, action=modified_prompt, total_task=overall_task,
                        current_task=current_task,
                        completed_task=completed_tasks, record_path=subagent_file, api_interval=api_interval)
    task_detail = {'subtask_name': current_task['subtask_name'], 'goal': current_task['goal']}
    if 'result_format' in current_task:
        task_detail['result_format'] = current_task['result_format']

    subagent.messages[0]['content'] += get_prompt(task_name=current_task['subtask_name'], task_detail=str(task_detail),
                                                  solution_num=2, rewrite=True, example_file=library_path, theta=theta,
                                                  use_detail=use_detail)
    agent_id += 1
    cur_sub_iter = 0
    try:
        error_times = 0
        while cur_sub_iter < sub_max_iter:
            print(f'cur_iter={cur_sub_iter}')
            cur_sub_iter += 1
            response = subagent.get_response()
            print(f'response {response}')
            text = response['content']
            functions = subagent.parse_functions(text)

            print(f'functions={functions}')
            if len(functions) == 0:
                print('no action')
                subagent.messages.append(
                    {'role': 'user',
                     'content': f'Available Actions:{subagent.action_apace}\nGive me the action between <action> and </action>.'})
                response = subagent.get_response()
                print(f'response {response}')
                text = response['content']
                # subagent.subtasks.extend(subagent.get_subtasks(text))
                functions = subagent.parse_functions(text)

            observation = 'No valid action found. Surround it by <action> and </action>'
            exec_function = None
            for function in functions:
                try:
                    if function['function_name'] == 'over':
                        break
                    elif function['function_name'] == 'subagent_handle':
                        function['args'].append(subagent)
                        function['args'].append(output_path)
                        function['args'].append(depth + 1)

                        subtask_name = function['args'][0]
                        subtask_idx = subagent.get_subtask_idx(subtask_name)
                        subagent.subtasks[subtask_idx]['result'] = observation

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
                subagent.messages = subagent.messages[:-((max_error_times - 1) * 2)]
                observation = f"For some unknown reason, this step cannot be completed with {name}. Try to solve this problem yourself."

            print(f'observation {observation}')
            if len(functions) > 0 and functions[0]['function_name'] == 'over':
                subagent.add_over_prompt()
                response = subagent.get_response()
                print(f'response {response}')
                text = response['content']

                result = subagent.get_result(text)
                process = subagent.get_process(text)
                if verify:
                    verify_agent = VerifyAgent(model_name=model_name, total_task=overall_task,
                                               current_task=current_task,
                                               completed_task=completed_tasks,
                                               process=process, result=result,
                                               record_path=f'verify_agent_{agent_id}.json')
                    response = verify_agent.get_response()
                    text = response['content']
                    functions = verify_agent.parse_functions(text)
                    if len(functions) == 0 or functions[0]['function_name'] == 'success':
                        pass
                    elif functions[0]['function_name'] == 'fail':
                        subagent.add_verify_prompt(check_ans=functions[0]['args'][0])
                        response = subagent.get_response()
                        text = response['content']
                if extend:
                    extend_skill(agent_file=subagent_file)
                break
            if error_times > 0:
                subagent.add_user_error_prompt(observation)
            else:
                subagent.add_user_prompt(observation)
    except openai.error.InvalidRequestError as e:
        print(f'{e} InvalidRequestError. Context length error?')
        for idx in range(len(subagent.messages) - 1, 0, -1):
            if subagent.messages[idx]["role"] == "user":
                break
        subagent.messages = subagent.messages[:idx - 2]  # 从后往前删掉idx:user, idx-1:assistant, idx-2:user
        subagent.messages.append({'role': 'user',
                                  'content': 'Give me the result immediately. Surrounded it with <result> and </result>'})
        response = subagent.get_response()
        text = response['content']

    if cur_sub_iter >= sub_max_iter:
        subagent.messages[-1] = {'role': 'user',
                                 "content": "Give me the final result of the subtask immediately, regardless of whether certain restrictions are met. Surrounded it with <result> and </result> If all conditions cannot be perfectly met, please return a result that is as appropriate as possible instead of an empty result."
                                 }
        response = subagent.get_response()
        text = response['content']

    result = subagent.get_result(text)
    return result


def subagent_handle(task_name, agent: MainAgent, output_path, depth=1):
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


def run_item(task, output_path="."):
    global skills, skills_save
    skills = copy.deepcopy(skills_save)

    max_iter = 10
    global agent_id
    if type == 3:
        from agents.main_agent.prompt import EXAMPLE_MESSAGES_3
        main_agent = MainAgent(model_name=model_name, task=task,
                               record_path=f'{output_path}/main_agent_{agent_id}_record.json',
                               example_message=EXAMPLE_MESSAGES_3)
    elif type == 2:
        from agents.main_agent.prompt import EXAMPLE_MESSAGES_2
        main_agent = MainAgent(model_name=model_name, task=task,
                               record_path=f'{output_path}/main_agent_{agent_id}_record.json',
                               example_message=EXAMPLE_MESSAGES_2)
    else:
        from agents.main_agent.prompt import EXAMPLE_MESSAGES
        main_agent = MainAgent(model_name=model_name, task=task,
                               record_path=f'{output_path}/main_agent_{agent_id}_record.json',
                               example_message=EXAMPLE_MESSAGES)

    agent_id += 1
    cur_iter = 0
    completed = False
    try:
        while cur_iter < max_iter:
            cur_iter += 1
            response = main_agent.get_response()
            text = response['content']
            functions = main_agent.parse_functions(text)
            if len(functions) == 0:
                print('no action')
                main_agent.messages.append(
                    {'role': 'user',
                     'content': f'Available actions:{main_agent.get_action_space()}\nGive me the action between <action> and </action>.'})
                response = main_agent.get_response()
                text = response['content']
                functions = main_agent.parse_functions(text)

            if len(functions) == 0:
                functions.append({'function_name': 'over', 'args': []})

            if functions[0]['function_name'] == 'subagent_handle':
                functions[0]['args'].append(main_agent)
                functions[0]['args'].append(output_path)
                observation = invoke_function(functions[0])
                main_agent.add_user_prompt(observation)

                subtask_name = functions[0]['args'][0]
                subtask_idx = main_agent.get_subtask_idx(subtask_name)
                if subtask_idx >= 0:
                    main_agent.subtasks[subtask_idx]['result'] = observation

            elif functions[0]['function_name'] == 'over':
                completed = True
                main_agent.add_over_prompt()
                response = main_agent.get_response()
                text = response['content']
                break
            else:
                main_agent.messages.append(
                    {'role': 'user',
                     'content': f'No valid action Found. Available actions:{main_agent.get_action_space()}\nGive me the action between <action> and </action>.'})

        if cur_iter >= max_iter:
            main_agent.add_over_prompt()
            response = main_agent.get_response()
            text = response['content']

    except openai.error.InvalidRequestError as e:
        for idx in range(len(main_agent.messages) - 1, 0, -1):
            if main_agent.messages[idx]["role"] == "user":
                break
        main_agent.messages = main_agent.messages[:idx - 2]  # 从后往前删掉idx:user, idx-1:assistant, idx-2:user
        main_agent.add_over_prompt()
        response = main_agent.get_response()
        text = response['content']

    check_result = check_plan_format(text)
    if check_result == "All formats are correct." and completed:
        skills_save = skills
        with open(library_path, 'w', encoding='utf-8') as f:
            json.dump(skills_save, f, indent=4)
        with open(f"{output_path}/skill.json", 'w', encoding='utf-8') as f:
            json.dump(skills_save, f, indent=4)

    if "No valid plan format found." in check_result:
        main_agent.messages.append({"role": "user", "content": f"{check_result}"})
        response = main_agent.get_response()
        text = response['content']
        check_result = check_plan_format(text)
    if check_result != "All formats are correct.":
        main_agent.messages.append({"role": "user", "content": f"{check_result}"})
        response = main_agent.get_response()
        text = response['content']
    plan_strs = get_content_list(text, begin_str='<plan>', end_str='</plan>')

    return plan_strs, completed


def run(type, task_ids, extend_end=999):
    output_dir = f'./output/travel/{method}/{model_name}/type{type}'
    data_path = f'./data/travel/data_type{type}.json'

    with open(data_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    global extend
    for task_id, d in enumerate(data):
        if task_id < extend_end:
            extend = True
        else:
            extend = False
        if task_id not in task_ids:
            continue
        print(f'data_idx={task_id}:{time.localtime()}')
        prediction = []
        # try:
        global agent_id
        agent_id = 0
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
    begin = 0
    end = 999
    step = 1
    extend_end = extend_ends[type-1]
    task_ids = range(begin, end, step)
    run(type, task_ids, extend_end=extend_end)
