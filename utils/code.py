import re

def get_content(s, begin_str='[BEGIN]', end_str='[END]'):
    _begin = s.find(begin_str)
    _end = s.find(end_str)
    if _begin == -1 or _end == -1:
        return ''
    else:
        return s[_begin + len(begin_str):_end].strip()

def get_content_list(s, begin_str='[BEGIN]', end_str='[END]'):
    result = []
    _begin = s.find(begin_str)
    if _begin>=0:
        _end = s[_begin + len(begin_str):].find(end_str) + _begin + len(begin_str)
    else:
        _end = s.find(end_str)
    while not (_begin == -1 or _end == -1):
        result.append(s[_begin + len(begin_str):_end].strip())
        s = s[_end + len(end_str):]
        _begin = s.find(begin_str)
        _end = s.find(end_str)
    unique_result = []
    for item in result:
        if item not in unique_result:
            unique_result.append(item)
    return unique_result


def string_to_function(string):
    exec(string, globals())
    return globals()[string.split(' ')[1].split('(')[0]]
