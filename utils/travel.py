import json

import requests
from utils.config_manager import ConfigManager
import ast
import re

config_manager = ConfigManager()


def action(action_str):
    try:
        print(f'action={action_str}')
        result = eval(action_str)
        return result
    except Exception as e:
        return f"An error occurred: {e}"


def query_database(query: list):
    config_manager.clear_proxies()
    try:
        response = requests.post(
            "http://localhost:8079/tools/database",
            json={'queries': query}
        )
        response = response.json()
        if len(response) > 0:
            response = response[0]
    except Exception as e:
        response = {'result': f'error', 'error': f'run error{e}'}
        print(response)
    config_manager.apply_proxies()
    return json.dumps(response)
    # return re.sub(r'\\n', '\n', str(response))



def execute_sql(statement: str):
    return query_database([statement])


def execute_python(code: str):
    config_manager.clear_proxies()
    response = requests.post(
        'http://127.0.0.1:8079/tools/python',
        json={'code': code}
    )
    config_manager.apply_proxies()
    result=response.json()
    return json.dumps(result)
    # return str(result)


def is_error(observation: str) -> bool:
    try:
        obs_json = json.loads(observation)
        return 'error' in obs_json and obs_json['error'] != ""
    except json.JSONDecodeError:
        return False

import re
from datetime import datetime

def check_plan_format(input_str):
    matches = re.findall(r'<plan>(\w+)\((.*?)\)</plan>', input_str)
    if not matches:
        return "No valid plan format found. Surround the plan in <plan> and </plan>"

    format_requirements = {
        'stay_in': ['str', 'time', 'time'],
        'visit': ['str', 'time', 'time'],
        'go_to_place': ['str', 'str', 'time', 'time'],
        'go_to_city': ['str', 'str', 'time', 'time', 'str']
    }

    errors = []

    if len(matches) == 0:
        return "Please provide a plan surrounded by <plan> and </plan> in the specified format."

    for method_name, params_str in matches:
        params = params_str.split(',')

        if method_name not in format_requirements:
            err_msg = f"Illegal plan: {method_name}."
            if err_msg not in errors:
                errors.append(err_msg)
            continue

        if len(params) != len(format_requirements[method_name]):
            err_msg = f"Incorrect number of parameters for {method_name}."
            if err_msg not in errors:
                errors.append(err_msg)
            continue

        for i, param in enumerate(params):
            param = param.strip()
            expected_format = format_requirements[method_name][i]

            if expected_format == 'str' and param.count('"') != 2:
                err_msg = f'Error in {method_name}: {param} should be surrounded by double quotes.'
                if err_msg not in errors:
                    errors.append(f'Error in {method_name}: {param} should be surrounded by double quotes.')

            if expected_format == 'time':
                try:
                    time_value = param.split('"')[1]
                    datetime.strptime(time_value, "%Y-%m-%d %H:%M")
                except (ValueError, IndexError):
                    err_msg = f'Error in {method_name}: {param} should be formatted as "%Y-%m-%d %H:%M".'
                    if err_msg not in errors:
                        errors.append(err_msg)

    return "\n".join(errors) if errors else "All formats are correct."
