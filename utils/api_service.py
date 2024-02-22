import json
import requests
import os
import openai
import time
import numpy as np

key_idx=0
keys=None

def set_keys(new_keys):
    global keys
    keys = new_keys

def chat_gpt(messages, model_name="gpt-3.5-turbo", sleep_time=20, temperature=0,proxy=None):
    if proxy is not None:
        os.environ["http_proxy"] = proxy
        os.environ["https_proxy"] = proxy
    if keys is not None:
        global key_idx
        key_idx+=1
        key_idx=key_idx%len(keys)
        os.environ["OPENAI_API_KEY"]=keys[key_idx]
        print(f'key={os.getenv("OPENAI_API_KEY")[:10]}')
    openai.api_key = os.getenv("OPENAI_API_KEY")
    org=os.getenv("OPENAI_ORGANIZATION")
    print(f'message[-1]={messages[-1]}')
    if org is not None:
        openai.organization=org
    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            timeout=60
        )
    # except openai.error.RateLimitError as e:
    #     print(e)
    #     time.sleep(60)
    #     response = openai.ChatCompletion.create(
    #         model=model_name,
    #         messages=messages,
    #         temperature=temperature,
    #         timeout=60
    #     )
    except openai.error.Timeout as e5:
        print(e5)
        time.sleep(60)
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            timeout=60
        )
    except openai.error.APIConnectionError as e4:
        print(e4)
        time.sleep(60)
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            timeout=60
        )

    except openai.error.ServiceUnavailableError as e2:
        print(e2)
        time.sleep(60)
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            timeout=60
        )
    except openai.error.APIError as e3:
        print(e3)
        time.sleep(60)
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            timeout=60
        )
    print(f'response={response}')
    time.sleep(sleep_time)
    if proxy is not None:
        os.environ.pop("http_proxy", None)
        os.environ.pop("https_proxy", None)
    return response['choices'][0]['message']


def get_init_chat():
    return [
        {"role": "system", "content": "You are a helpful assistant."}
    ]


def get_token_num(text):
    from transformers import GPT2Tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    tokens = tokenizer.encode(text)
    return len(tokens)