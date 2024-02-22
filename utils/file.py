import json


def jsonl_to_json(jsonl_file_path, json_file_path):
    data = []
    with open(jsonl_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data.append(json.loads(line))

    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def json_to_jsonl(json_file_path, jsonl_file_path, filter_func=lambda x: True):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    data = [d for d in data if filter_func(d)]

    with open(jsonl_file_path, 'w', encoding='utf-8') as file:
        for entry in data:
            json.dump(entry, file, ensure_ascii=False)
            file.write('\n')


def merge_json(file_list, output_file):
    data_all = []
    for f in file_list:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            data_all.extend(data)

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data_all, file, ensure_ascii=False, indent=4)


def get_json_refined(json_str):
    formatted_str = ''
    in_double_quotes = False
    for char in json_str:
        if char == '"' and not in_double_quotes:
            in_double_quotes = True
        elif char == '"' and in_double_quotes:
            in_double_quotes = False

        if char == "'" and not in_double_quotes:
            formatted_str += '"'
        else:
            formatted_str += char

    json_object = json.loads(formatted_str)
    return json_object