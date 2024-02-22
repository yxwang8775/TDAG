# This code should be run in ADAPT envirenment.
import os
import time

import openai
import sys
import json
import re
from tqdm import tqdm
from tenacity import (
    retry,
    stop_after_attempt,  # type: ignore
    wait_random_exponential,  # type: ignore
    RetryError
)
import copy
import ast


openai.api_key = "sk-"
LM = 'gpt-3.5-turbo-0613'

max_depth = 3
# page_len = 3
page_len = 5
max_update_times = 3

output = open('run_webshop_TDAG.txt', 'w')
# 将标准输出重定向到文件
sys.stdout = output

host_ip = "172.29.0.1"
WEBSHOP_URL = "http://127.0.0.1:3000"

# host_ip="127.0.0.1"
# WEBSHOP_URL="http://172.29.2.41:3000"


proxy = f"http://{host_ip}:10809"


def chat_gpt(messages, model_name="gpt-3.5-turbo", sleep_time=5, temperature=0, proxy=None, **kwargs):
    if proxy is not None:
        os.environ["http_proxy"] = proxy
        os.environ["https_proxy"] = proxy

    # openai.api_key = os.getenv("OPENAI_API_KEY")
    # org = os.getenv("OPENAI_ORGANIZATION")

    org = None
    print(f'message[-1]={messages[-1]}')
    if org is not None:
        openai.organization = org
    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            timeout=60,
            **kwargs
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
            timeout=60,
            **kwargs
        )
    # except openai.error.APIConnectionError as e4:
    #     print(e4)
    #     time.sleep(60)
    #     response = openai.ChatCompletion.create(
    #         model=model_name,
    #         messages=messages,
    #         temperature=temperature,
    #         timeout=60,
    #         **kwargs
    #     )
    #
    # except openai.error.ServiceUnavailableError as e2:
    #     print(e2)
    #     time.sleep(60)
    #     response = openai.ChatCompletion.create(
    #         model=model_name,
    #         messages=messages,
    #         temperature=temperature,
    #         timeout=60,
    #         **kwargs
    #     )
    # except openai.error.APIError as e3:
    #     print(e3)
    #     time.sleep(60)
    #     response = openai.ChatCompletion.create(
    #         model=model_name,
    #         messages=messages,
    #         temperature=temperature,
    #         timeout=60,
    #         **kwargs
    #     )
    print(f'response={response}')
    time.sleep(sleep_time)
    if proxy is not None:
        os.environ.pop("http_proxy", None)
        os.environ.pop("https_proxy", None)
    return response['choices'][0]['message']


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(15))
def llm(prompt, stop=["\n"], max_tokens=100):
    os.environ["https_proxy"] = proxy
    os.environ["http_proxy"] = proxy
    response = openai.ChatCompletion.create(
        model=LM,
        messages=[
            {"role": "system", "content": 'You are a helpful assistant navigating through a shopping website'},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=max_tokens,
        # top_p=1,
        # frequency_penalty=0.0,
        # presence_penalty=0.0,
        stop=stop
    )
    choices = response["choices"]
    completion_objs = [choice.message for choice in choices]
    completions = [completion.content for completion in completion_objs]

    os.environ.pop("http_proxy", None)
    os.environ.pop("https_proxy", None)

    return completions[0]


PLANNER_INIT_MESSAGES = [
    {"role": "system", "content": f'''You are an agent that navigates a shopping website. You are given the task of buying a product that satisfies a mentioned criteria. Your job is to come up with an abstract plan to successfully finish the task. You have access to the following modules to do specific tasks:
- Search[query]: Mention a query keywords to put into search bar. Brings you to the search page with only {page_len} most relevant products displayed.
- SimpleMatch[criteria]: Runs a superficial check based on product title and price to return a list products on the search page that exactly match the criteria. If information about any sub-criteria cannot be determined or do not match, the product is not included. If the criteria is very complex, it will likely fail and return an empty list. 
- DetailMatch[prod_id, criteria]: Tells you if a product with given prod_id, exactly matches your criteria (string).
- Buy[prod_id, criteria]: For the product, select the options such as size and color that best match the criteria.
To conduct search, design query based on the fact you will see the search page with only {page_len} top relevant items. There is no filter based on price in the search bar. Argument 'prod_id' denotes product id, it starts with B, and is an alphanumeric string of length 10.
'''}
]


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(25))
def plan_llm(prompt, init_messages=None):
    if init_messages is None:
        init_messages = PLANNER_INIT_MESSAGES
    os.environ["https_proxy"] = proxy
    os.environ["http_proxy"] = proxy
    if isinstance(prompt, list): prompt = prompt[0]
    init_prmpt = f'''You are an agent that navigates a shopping website. You are given the task of buying a product that satisfies a mentioned criteria. Your job is to come up with an abstract plan to successfully finish the task. You have access to the following modules to do specific tasks:
- Search[query]: Mention a query keywords to put into search bar. Brings you to the search page with only {page_len} most relevant products displayed.
- SimpleMatch[criteria]: Runs a superficial check based on product title and price to return a list products on the search page that exactly match the criteria. If information about any sub-criteria cannot be determined or do not match, the product is not included. If the criteria is very complex, it will likely fail and return an empty list. 
- DetailMatch[prod_id, criteria]: Tells you if a product with given prod_id, exactly matches your criteria (string).
- Buy[prod_id, criteria]: For the product, select the options such as size and color that best match the criteria.
To conduct search, design query based on the fact you will see the search page with only {page_len} top relevant items. There is no filter based on price in the search bar. Argument 'prod_id' denotes product id, it starts with B, and is an alphanumeric string of length 10.
'''
    print(f"in plan_llm\nprompt={prompt}")
    messages = copy.deepcopy(init_messages)
    messages.append({"role": "user", "content": prompt})

    response = openai.ChatCompletion.create(
        model=LM,
        messages=[
            {"role": "system", "content": init_prmpt},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=800,
        # top_p=1,
        # frequency_penalty=0.0,
        # presence_penalty=0.0,
    )
    choices = response["choices"]
    completion_objs = [choice.message for choice in choices]
    completions = [completion.content for completion in completion_objs]
    os.environ.pop("http_proxy", None)
    os.environ.pop("https_proxy", None)
    print(f"response={completions[0]}")
    return completions[0]


import requests
from bs4 import BeautifulSoup
from bs4.element import Comment

ACTION_TO_TEMPLATE = {
    'Description': 'description_page.html',
    'Features': 'features_page.html',
    'Reviews': 'review_page.html',
    'Attributes': 'attributes_page.html',
}


def clean_str(p):
    return p.encode().decode("unicode-escape").encode("latin1").decode("utf-8")


def tag_visible(element):
    ignore = {'style', 'script', 'head', 'title', 'meta', '[document]'}
    return (
            element.parent.name not in ignore and not isinstance(element, Comment)
    )


def webshop_text(session, page_type, query_string='', page_num=1, asin='', options={}, subpage='', **kwargs):
    print(f"in webshop_text")

    if page_type == 'init':
        url = (
            f'{WEBSHOP_URL}/{session}'
        )
    if page_type == 'search':
        url = (
            f'{WEBSHOP_URL}/search_results/{session}/'
            f'{query_string}/{page_num}'
        )
    elif page_type == 'item':
        url = (
            f'{WEBSHOP_URL}/item_page/{session}/'
            f'{asin}/{query_string}/{page_num}/{options}'
        )
    elif page_type == 'item_sub':
        url = (
            f'{WEBSHOP_URL}/item_sub_page/{session}/'
            f'{asin}/{query_string}/{page_num}/{subpage}/{options}'
        )
    elif page_type == 'end':
        url = (
            f'{WEBSHOP_URL}/done/{session}/'
            f'{asin}/{options}'
        )
    html = requests.get(url).text
    html_obj = BeautifulSoup(html, 'html.parser')
    texts = html_obj.findAll(text=True)
    visible_texts = list(filter(tag_visible, texts))

    if False:
        # For `simple` mode, return just [SEP] separators
        return ' [SEP] '.join(t.strip() for t in visible_texts if t != '\n')
    else:
        # Otherwise, return an observation with tags mapped to specific, unique separators
        observation = ''
        option_type = ''
        options = {}
        asins = []
        cnt = 0
        prod_cnt = 0
        just_prod = 0
        for t in visible_texts:
            if t == '\n': continue
            if t.replace('\n', '').replace('\\n', '').replace(' ', '') == '': continue

            if t.parent.name == 'button':  # button
                processed_t = f'\n[{t}] '
            elif t.parent.name == 'label':  # options
                if f"'{t}'" in url:
                    processed_t = f'[[{t}]]'
                else:
                    processed_t = f'[{t}]'
                options[str(t)] = option_type
            elif t.parent.get('class') == ["product-link"]:  # product asins
                processed_t = f'\n[{t}] '
                if prod_cnt >= 10:
                    processed_t = ''
                prod_cnt += 1
                asins.append(str(t))
                just_prod = 0
            else:  # regular, unclickable text
                processed_t = '\n' + str(t) + ' '
                if cnt < 2 and page_type != 'init': processed_t = ''
                if just_prod <= 2 and prod_cnt >= page_len + 1: processed_t = ''
                option_type = str(t)
                cnt += 1
            just_prod += 1
            observation += processed_t
        info = {}
        if options:
            info['option_types'] = options
        if asins:
            info['asins'] = asins
        if 'Your score (min 0.0, max 1.0)' in visible_texts:
            idx = visible_texts.index('Your score (min 0.0, max 1.0)')
            info['reward'] = float(visible_texts[idx + 1])
            observation = 'Your score (min 0.0, max 1.0): ' + (visible_texts[idx + 1])
        print(f"observation={observation}\ninfo={info}\nurl={url}")
        return clean_str(observation), info, url


class webshopEnv:
    def __init__(self):
        self.sessions = {}
        self.url_history = {}

    def clone_state(self):
        return copy.deepcopy(self.sessions)

    def step(self, session, action):
        done = False
        observation_ = None
        if action == 'reset':
            self.sessions[session] = {'session': session, 'page_type': 'init'}
        elif action == 'load':
            self.sessions[session] = self.sessions[session]
        elif action.startswith('think['):
            observation = 'OK.'
        elif action.startswith('search['):
            assert self.sessions[session]['page_type'] == 'init'
            query = action[7:-1]
            self.sessions[session] = {'session': session, 'page_type': 'search',
                                      'query_string': query, 'page_num': 1}
        elif action.startswith('click['):
            button = action[6:-1]
            if button == 'Buy Now':
                assert self.sessions[session]['page_type'] == 'item'
                self.sessions[session]['page_type'] = 'end'
                done = True
            elif button == 'Back to Search':
                assert self.sessions[session]['page_type'] in ['search', 'item_sub', 'item']
                self.sessions[session] = {'session': session, 'page_type': 'init'}
            elif button == 'Next >':
                # assert False # ad hoc page limitation
                assert self.sessions[session]['page_type'] == 'search'
                self.sessions[session]['page_num'] += 1
            elif button == '< Prev':
                assert self.sessions[session]['page_type'] in ['search', 'item_sub', 'item']
                if self.sessions[session]['page_type'] == 'search':
                    # assert False
                    self.sessions[session]['page_num'] -= 1
                elif self.sessions[session]['page_type'] == 'item_sub':
                    self.sessions[session]['page_type'] = 'item'
                elif self.sessions[session]['page_type'] == 'item':
                    self.sessions[session]['page_type'] = 'search'
                    self.sessions[session]['options'] = {}
            elif button in ACTION_TO_TEMPLATE:
                assert self.sessions[session]['page_type'] == 'item'
                self.sessions[session]['page_type'] = 'item_sub'
                self.sessions[session]['subpage'] = button
            else:
                if self.sessions[session]['page_type'] == 'search':
                    assert button in self.sessions[session].get('asins', [])  # must be asins
                    self.sessions[session]['page_type'] = 'item'
                    self.sessions[session]['asin'] = button
                elif self.sessions[session]['page_type'] == 'item':
                    assert 'option_types' in self.sessions[session]
                    assert button in self.sessions[session]['option_types'], (
                        button, self.sessions[session]['option_types'])  # must be options
                    option_type = self.sessions[session]['option_types'][button]
                    if not 'options' in self.sessions[session]:
                        self.sessions[session]['options'] = {}
                    self.sessions[session]['options'][option_type] = button
                    observation_ = f'You have clicked {button}.'
        else:
            assert False
        observation, info, url = webshop_text(**self.sessions[session])
        if action == 'reset': observation = observation.replace('Instruction:  \n',
                                                                'Instruction:  \nI am looking to buy a product. ')
        if observation_:
            observation = observation_
        self.sessions[session].update(info)
        reward = info.get('reward', 0.0)
        return observation, reward, done,


env = webshopEnv()


def custom_webshop_run(idx, prompt, env, to_print=True):
    print(f"in custom_webshop_run")
    print(f"begin custom_webshop_run\nidx={idx}\nprompt={prompt}\ne n d\nenv={env}")
    ## Assumption is that task is contained in the prompt.
    init_prompt = prompt
    prompt = ''
    history = []
    act_history = []
    pat_ctr = 0
    max_pat = 3
    done = False
    observation = ''
    action = "load"
    for i in range(15):
        try:
            if not (action.startswith('think') or action.startswith('load') or action == 'reset'): act_history.append(
                action)
            res = env.step(idx, action)
            observation = res[0]
            pat_ctr = 0

        except AssertionError:
            observation = 'Invalid action! Try a different action.'
            pat_ctr += 1

        if action.startswith('think'):
            observation = 'OK.'

        if 'load' in action or 'reset' in action:
            observation = observation

        if to_print:
            print(f'Action: {action}\nObservation: {observation}\n')
            sys.stdout.flush()
        if i:
            prompt += f' {action}\nObservation: {observation}\n\nAction:'
        else:
            prompt += f'{observation}\n\nAction:'

        history.append(f'Action: {action}\nObservation: {observation}')

        if pat_ctr >= max_pat:
            print('exhausted patience')
            break

        if res[2] or (action.startswith('think') and (
                'task completed' in action.lower() or 'task failed' in action.lower())):  # Finds the done variable, gives reward
            done = True
            return (res[0], res[1], done), history, act_history

        action = llm(init_prompt + prompt[-(6400 - len(init_prompt)):], stop=['\n']).lstrip(
            ' ')  # History is being shortened
        print(f"res[0]={res[0]}\nhistory={history}\nact_history={act_history}")
    return (res[0], 0, done), history, act_history


def load_checkpoint(idx, ckpt):
    alt_env = webshopEnv()
    for act in ckpt:
        res = alt_env.step(idx, act)
        print(act)
        print(res)
        print(alt_env.sessions[idx])
        print('------')


plan_LM_examples = {
    "level_1": '''Information from previous run: -
Goal: Buy 3 ounce bottle of citrus deodorant for sensitive skin, that is natural and priced less than 50.00 dollars.
# Think: Based on the criteria and the search bar, I should query “3 ounce citrus deodorant sensitive skin”. I have the following constraints: “natural and price lower than $30” which I can use to narrow down search results.
Step 1: Search[“3 ounce citrus deodorant sensitive skin”]
# Think: Now I will need to narrow down the search results for price lower than $30 and natural
Step 2: SimpleMatch[“3 ounce citrus deodorant sensitive skin with price lower than $50 and natural”]
# Think: Since it returns a list of up to 3 products, I will pick the first suitable product. For now, I’ll denote its id as prod_id for placeholder.
Step 3: Buy[prod_id, "3 ounce bottle of citrus deodorant for sensitive skin, that is natural and priced less than 30.00 dollars"]
#Think: My plan requrires all these steps to succeed sequentially, so I will use the "AND" operator.
Execution Order: (Step 1 AND Step 2 AND Step 3)
''',

    'level_2': '''Information from previous run: 
- Unable to get matching product using: SimpleMatch[“3 ounce citrus deodorant sensitive skin with price lower than $30 and natural”]
- Search results page:
[Back to Search] 
Page 1 (Total results: 50) 
[Next >] 
[B078GWRC1J] 
Bright Citrus Deodorant by Earth Mama | Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B08KBVJ4XN] 
Barrel and Oak - Aluminum-Free Deodorant, Deodorant for Men, Essential Oil-Based Scent, 24-Hour Odor Protection, Cedar & Patchouli Blend, Gentle on Sensitive Skin (Mountain Sage, 2.7 oz, 2-Pack) 
$35.95 
[B078GTKVXY] 
Ginger Fresh Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B08SMG4WB9] 
Each & Every 2-Pack Natural Aluminum-Free Deodorant for Sensitive Skin with Essential Oils, Plant-Based Packaging (Citrus & Vetiver, 2.5 Ounce (Pack of 2)) 
$25.0 
[B08KVCCSD6] 
Each & Every 3-Pack, Natural Aluminum-Free Deodorant for Sensitive Skin Made with Essential Oils, 2.5 Oz. (Lavender & Lemon, Citrus & Vetiver, and Coconut & Lime) 
$35.0 
[B087WKSR2G] 

Goal: Narrow down search results for 3 ounce bottle of citrus deodorant for sensitive skin that is priced lower than $30 and natural. You cannot search again.
#Think: Based on the search results and previous information, SimpleMatch failed because my criteria was too complex. Price constraint is easy to verify, I will narrow down based on that first then examine in detail for “natural constraint”
#Think: Based on price, I narrow down my search to B078GWRC1J, B08SMG4WB9 as they look suitable. These are on my shortlist to examine the natural constraint  in detail one by one.
Step 1: DetailMatch[B078GWRC1J, 3 ounce bottle of  for sensitive skin, that is natural and priced less than 30.00 dollars]
Step 2: DetailMatch[B08SMG4WB9, 3 ounce bottle of citrus deodorantcitrus deodorant for sensitive skin, that is natural and priced less than 30.00 dollars]
#Think: If none of the products exactly match my criteria, I will search again with a new query that includes the natural criteria too. This ensures my plan is compelete.
Step 3: Search[3 ounce citrus deodrant natural and sensitive skin]
#Think: Since these steps are linked by an if condition, I only need one of them to succeed. I will connect them using the "OR" operator.
Execution Order: (Step 1 OR Step 2 OR Step 3)
'''

}

plan_prompt = 'Write an abstract plan to successfully complete the goal. In each step of the plan mention which module (including arguments) that need to be called. Learn from and incorporate information from previous runs, e.g. do not repeat previously successful or unsuccesful commands. Here are some examples:'
plan_prompt += '\n\n'.join(plan_LM_examples.values()) + '\n\n'
plan_prompt += '''Here is a new goal. Write an abstract plan to successfully complete the goal. In each step of the plan mention which module (including arguments) that need to be called. Learn from and incorporate information from previous runs, e.g. do not repeat previously successful or unsuccesful commands. In the end, output the intended execution order.

Information from previous run: {}
Goal: {}
'''

buy_prompt = """Instruction: Buy product [B078GWRC1J] that matches criteria: 3 ounce bottle of bright citrus deodorant for sensitive skin, and price lower than 50.00 dollars 

Action: think['I should be on the search page where I can see a list of products, I should verify that.']
Observation: OK.

Action: load
Observation:
[Back to Search] 
Page 1 (Total results: 50) 
[Next >] 
[B078GWRC1J] 
Bright Citrus Deodorant by Earth Mama | Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B08KBVJ4XN] 
Barrel and Oak - Aluminum-Free Deodorant, Deodorant for Men, Essential Oil-Based Scent, 24-Hour Odor Protection, Cedar & Patchouli Blend, Gentle on Sensitive Skin (Mountain Sage, 2.7 oz, 2-Pack) 
$35.95 
[B078GTKVXY] 
Ginger Fresh Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 

Action: think['I can spot product [B078GWRC1J] and it is a clickable link since its enclosed in square brackets. I should click on it.]
Observation: OK.

Action: click[B078GWRC1J]
Observation:
[Back to Search] 
[< Prev] 
scent [assorted scents][bright citrus][calming lavender][ginger fresh][simply non-scents]
size [travel set (4-pack)][3 ounce (pack of 1)][3-ounce (2-pack)]
Bright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
Price: $10.99 
Rating: N.A. 
[Description] 
[Features] 
[Reviews] 
[Buy Now]

Action: think[I'm already on the product page.  I see multiple possible options enclosed in '[]' for scent and size for this product. To match the input criteria, I should click on options '[bright citrus]' for scent and '[3 ounce (pack of 1)]' for size one by one and then buy in the end.]
Observation: OK.

Action: click[bright citrus]
Observation: You have clicked bright citrus. 

Action: click[3 ounce (pack of 1)]
Observation: You have clicked 3 ounce (pack of 1). 

Action: think[My task is to buy the product, for it should to click 'buy now']
Observation: OK.

Action: click[Buy Now]
Observation: You have clicked buy now.

Action: think[I finished buying the product. Task completed!]


Here is another task in which you need to buy a product. When you finish buying the product with the most relevant choices, use 'think[Task completed']. If you cannot find the matching options or proceed, think['Task failed']. Note that you can only click on text enclosed in '[]' on the webpage. Everything else is only a description, not valid with the "click" action.

Instruction: Buy product [{}] that matches the criteria: {}

"""

detail_match_prompt = '''You are given a webpage of an item on an online shopping website and a criteria. Your task is to answer if the product on the page exactly matches the criteria. Not the criteria could have multiple requirements that should be checked one by one and all must satisfy for an exact match.

Here are a few examples:

Criteria: 3 ounce bottle of citrus deodorant for sensitive skin that is priced lower than $30 and natural.
Item Page:
[Back to Search] 
[< Prev] 
scent [assorted scents][bright citrus][calming lavender][ginger fresh][simply non-scents]
size [travel set (4-pack)][3 ounce (pack of 1)][3-ounce (2-pack)]
Bright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
Price: $10.99 
Rating: N.A. 
[Description] 
Features:
 NEW from Earth Mama (formerly Earth Mama Angel Baby), formulated especially for pregnancy, breastfeeding and sensitive skin  
 Contains organic grapefruit, tangerine and calendula  
 NO propylene glycol, artificial fragrance, parabens or aluminum  
 Dermatologist tested and clinically tested for irritation  
 Better than natural organic! NSF/ANSI 305 Certified by Oregon Tilth   
[Reviews] 
[Attributes] 
[Buy Now] 

Answer: The product is available in 3 ounce size, is citrus and suitable for sensitive skin. It is also organic or natural. Its price is $10.99 which is less than $30.
Thus, the answer is True (exact match).

Criteria: 3 ounce bottle of citrus deodorant for sensitive skin that is priced lower than $30 and natural.
Item Page:
[Back to Search] 
[< Prev] 
size [3 ounce][3 ounce (pack of 1)]
unit count [2.0][3.0]
Barrel and Oak - Aluminum-Free Deodorant, Deodorant for Men, Essential Oil-Based Scent, 24-Hour Odor Protection, Cedar & Patchouli Blend, Gentle on Sensitive Skin (Mountain Sage, 2.7 oz, 2-Pack) 
Price: $15.95 
Rating: N.A. 
[Description] 
Features:
 About this item WHY ALUMINUM-FREE DEODORANT? Aluminum-free deodorants use more natural ingredients unlike antiperspirants, which use chemicals to block sweat. Safely fight odor for 24 hours with Barrel & Oak's deodorants—our gentle formula is easy on sensitive skin. START SMELLING LIKE THE MAN YOU WANT TO BE: Our mountain sage aluminum-free men's deodorant is naturally fragranced with an outdoorsy scent of crisp conifer, sage, & citrus—think sweet notes of citrus with earthy tones of cedar & patchouli. PREMIUM INGREDIENTS FOR NATURAL FRAGRANCES: Our deodorants for men are composed of natural, essential oil-based scents. These natural fragrance deodorants are more subtle than their synthetic counterparts, but they're better for you & the planet. DESIGNED FOR THE MODERN MAN: Barrel & Oak has a full spectrum of grooming & body care products that are designed with function, fragrance, & effective ingredients for the health-conscious & practical modern man. Give your body what it deserves. EARTH-FRIENDLY, YOU-FRIENDLY, WALLET-FRIENDLY: Our premium products for men are scented with natural fragrances & essential oils, free of parabens, phthalates, & SLS, packaged in recyclable materials, cruelty-free, & vegan or vegetarian.  
[Reviews] 
[Attributes] 
[Buy Now] 

Answer: The product is not citrus in nature. It does not match the criteria. It's price is $15.95 which is less than $30.
Thus, the answer is False (not an exact match).

Now here is the criteria and item page for the another task. Try you best to determine exact match, otherwise, respond with "False", i.e., no exact match. Generate an explanation before the answer to justify your decision.

Criteria: {}
Item Page:
{}
Answer: 
'''

list_match_prompt = '''You are given a search page on an online shopping site with a list of products along with name and price. Based on this information, your task is return a list of product IDs (enclosed in []) of all products that exactly match all requirements in the criteria. If the information provided is not enough to make a determination, return an empty list. 
Here are a few examples.

Search Page: 
[Back to Search] 
Page 1 (Total results: 50) 
[Next >] 
[B078GWRC1J] 
Bright Citrus Deodorant by Earth Mama | Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B08KBVJ4XN] 
Barrel and Oak - Aluminum-Free Deodorant, Deodorant for Men, Essential Oil-Based Scent, 24-Hour Odor Protection, Cedar & Patchouli Blend, Gentle on Sensitive Skin (Mountain Sage, 2.7 oz, 2-Pack) 
$35.95 
[B078GTKVXY] 
Ginger Fresh Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B08SMG4WB9] 
Each & Every 2-Pack Natural Aluminum-Free Deodorant for Sensitive Skin with Essential Oils, Plant-Based Packaging (Citrus & Vetiver, 2.5 Ounce (Pack of 2)) 
$25.0 
[B08KVCCSD6] 
Each & Every 3-Pack, Natural Aluminum-Free Deodorant for Sensitive Skin Made with Essential Oils, 2.5 Oz. (Lavender & Lemon, Citrus & Vetiver, and Coconut & Lime) 
$35.0 

Criteria: less than 5 ounce citrus deodorant sensitive skin, price less than $30.
Answer: My requirements are 5 ounce, citrus deodrant, suitable for sensitive skin, and price less than $30. Looks like this information is available on the search page, so I can proceed.
Products B078GWRC1J, B08SMG4WB9 look suitable as they are less than 5 ounce, citrus and have price 10.99 and $25 less than $30. Thus, shortlisted IDs are shortlisted=['B078GWRC1J', 'B08SMG4WB9']

Criteria: less than 5 ounce citrus deodorant sensitive skin, cruelty free.
Answer: My requirements are 5 ounce, citrus deodrant, suitable for sensitive skin, and cruelty-free. Since there is no information about cruelty free on the search page, I cannot proceed. Task failed!

Here is another task with a different search page and criteria. List all the product ids (enclosed in []) from the search page that match ALL the requirements in the criteria. Name this list shortlisted. If you cannot make the determination about even 1 sub-criteria, do not make a guess, output "task failed!". Generate an explanation before the answer to justify your decision.

Search Page:
{}

Criteria: {}
Answer: 
'''


def search(env, idx, query):
    hist = []
    if not env.sessions[idx]['page_type'] == 'init':
        res = env.step(idx, 'click[Back to Search]')
        hist.append('click[Back to Search]')
    res = env.step(idx, f'search[{query}]')
    hist.append(f'search[{query}]')
    return env, (res[0], res[1], True), {'a_hist': hist}


def buy(env, idx, prod_id, query):
    if not env.sessions[idx]['page_type'] == 'search': return env, (
        'Not on search page with list of items.', 0, False), {'a_hist': []}
    obs, _, _ = webshop_text(**env.sessions[idx])
    prompt = buy_prompt.format(prod_id, query)
    res, l_hist, a_hist = custom_webshop_run(idx, prompt, env, False)
    return env, (res[0], res[1], res[2]), {'a_hist': a_hist}


def list_match(env, idx, criteria):
    if not env.sessions[idx]['page_type'] == 'search': return env, ('Not on search page.', 0, False), {'a_hist': []}
    page, _, _ = webshop_text(**env.sessions[idx])
    prompt = list_match_prompt.format(page, criteria)
    response = llm(prompt, stop=['\n\n'], max_tokens=400)
    products = []
    if not ('task' in response.lower() and 'fail' in response.lower()) and 'shortlisted=' in response:
        products = response.split('shortlisted=')[-1].rstrip('.')
        products = ast.literal_eval(products)
        return env, (page, 0, True), {'product': products, 'a_hist': [
            'think[Does any product on the list page exactly match the search criteria?]']}
    else:
        return env, (page, 0, False), {'product': [], 'a_hist': [
            'think[Does any product on the list page exactly match the search criteria?]']}


def detail_match(env, idx, prod_id, criteria):
    if not env.sessions[idx]['page_type'] == 'search': return env, ('Not on search page.', 0, False), {'a_hist': []}
    obs, _, _ = webshop_text(**env.sessions[idx])
    actions = []
    if f'[{prod_id}]' in obs:
        actions.append(f'think[I should check if {prod_id} matches my desired criteria in detail.]')
        res = env.step(idx, f'click[{prod_id}]')
        actions.append(f'click[{prod_id}]')
        if not env.sessions[idx]['page_type'] == 'item': return env, (
            'Landed on unexpected page. Expected: item', 0, False), {'a_hist': []}
        item_page = res[0]
        res = env.step(idx, 'click[Features]')
        actions.append('click[Features]')
        prod_feat = 'Features:\n ' + res[0].lstrip('[Back to Search]\n[< Prev]\n')
        _ = env.step(idx, 'click[< Prev]')
        actions.append('click[< Prev]')
        item_page = item_page.replace('[Features]', prod_feat)

        prompt = detail_match_prompt.format(criteria, item_page)
        response = llm(prompt, stop=['\n\n'])
        try:
            answer = "true" in response.lower().split('answer')[-1]
        except:
            answer = False
        if not env.sessions[idx]['page_type'] == 'item': return env, (
            'Landed on unexpected page. Expected: item', 0, False), {'a_hist': []}
        res = env.step(idx, 'click[< Prev]')
        actions.append('click[< Prev]')
        return env, (res[0], 0, answer), {'product': [prod_id], 'a_hist': actions}
    return env, (obs, 0, False), {'product': [], 'a_hist': actions}


def executor(env, idx, step_out, running_prods=[]):  # Need to return a success and done variable
    print(f"in executor\nenv={env}\nidx={idx}\nstepout={step_out}running_prods={running_prods}")
    if 'Search' in step_out:
        query = re.findall(r"\[(.*?)\]", step_out)[0]
        return search(env, idx, query)
    elif 'SimpleMatch' in step_out:
        query = re.findall(r"\[(.*?)\]", step_out)[0]
        return list_match(env, idx, query)
    elif 'Buy' in step_out:
        args = re.findall(r"\[(.*?)\]", step_out)[0]
        prod, query = args.split(',')[0], ' '.join(args.split(',')[1:])
        if len(running_prods): prod = running_prods[0]
        if not prod.startswith('B') and len(prod) == 10: return env, (
            'Invalid first argument to Buy, expecting product id', 0, False), {'product': [], 'a_hist': []}
        return buy(env, idx, prod, query)
    elif 'DetailMatch' in step_out:
        args = re.findall(r"\[(.*?)\]", step_out)[0]
        prod, query = args.split(',')[0], ' '.join(args.split(',')[1:])
        if not prod.startswith('B') and len(prod) == 10:  return env, (
            'Invalid first argument to DetailMatch, expecting product id', 0, False), {'product': [], 'a_hist': []}
        return detail_match(env, idx, prod, query)
    else:
        return AssertionError


def plan_to_args(plan, keyword='Step', lkey='execution order'):
    args = []
    lines = plan.split('\n')
    for line in lines:
        if line.startswith(keyword): args.append(re.sub(r'{} \d+: '.format(keyword), '', line))
        if lkey in line.lower():
            logic = line.split(': ')[-1]
    args_lookup = {i + 1: args[i] for i in range(len(args))}
    try:
        return fetch_args(args_lookup, parse_expression(logic))
    except:
        return {'steps': args, 'logic': 'AND'}


def parse_expression(expression):
    stack = []
    current = {}
    for token in re.findall(r'Step \d+|AND|OR|\(|\)', expression):
        if token.startswith('Step'):
            if 'steps' not in current:
                current['steps'] = []
            current['steps'].append(int(token.split()[1]))
        elif token in ('AND', 'OR'):
            current['logic'] = token
        elif token == '(':
            stack.append(current)
            current = {}
        elif token == ')':
            closed = current
            current = stack.pop()
            if 'steps' not in current:
                current['steps'] = []
            current['steps'].append(closed)
    return current


def fetch_args(args_lookup, logic_exp):
    out = copy.deepcopy(logic_exp)
    assert 'steps' in logic_exp.keys()
    for s, step in enumerate(logic_exp['steps']):
        if isinstance(step, int):
            out['steps'][s] = args_lookup[step]
        elif isinstance(step, dict):
            out['steps'][s] = fetch_args(args_lookup, step)
    return out


prompt1 = """Webshop 
Instruction:  
i would like a 3 ounce bottle of bright citrus deodorant for sensitive skin, and price lower than 50.00 dollars 
[Search]  

Action: search[3 ounce bright citrus deodorant sensitive skin]
Observation: 
[Back to Search] 
Page 1 (Total results: 50) 
[Next >] 
[B078GWRC1J] 
Bright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B078GTKVXY] 
Ginger Fresh Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B08KBVJ4XN] 
Barrel and Oak - Aluminum-Free Deodorant, Deodorant for Men, Essential Oil-Based Scent, 24-Hour Odor Protection, Cedar & Patchouli Blend, Gentle on Sensitive Skin (Mountain Sage, 2.7 oz, 2-Pack) 
$15.95  

Action: think[B078GWRC1J and B078GTKVXY are bright citrus deodorant less then 50 dollars. I can check B078GWRC1J first.]
Observation: OK.

Action: click[B078GWRC1J]
Observation: 
[Back to Search] 
[< Prev] 
scent [assorted scents][bright citrus][calming lavender][ginger fresh][simply non-scents]
size [travel set (4-pack)][3 ounce (pack of 1)][3-ounce (2-pack)]
Bright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
Price: $10.99 
Rating: N.A. 
[Description] 
[Features] 
[Reviews] 
[Buy Now]  

Action: think[For 3 ounce bottle of bright citrus deodorant for sensitive skin, the item has options 'bright citrus' and '3 ounce (pack of 1)' and seems good to buy.]
Observation: OK.

Action: click[bright citrus]
Observation: You have clicked bright citrus. 

Action: click[3 ounce (pack of 1)]
Observation: You have clicked 3 ounce (pack of 1). 

Action: click[Buy Now]
"""

prompt2 = """Webshop 
Instruction:  
i would like a 3 ounce bottle of bright citrus deodorant for sensitive skin, and price lower than 50.00 dollars 
[Search]  

Action: search[3 ounce bright citrus deodorant sensitive skin price under 50.0]
Observation: 
[Back to Search] 
Page 1 (Total results: 50) 
[Next >] 
[B078GWRC1J] 
Bright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B078GTKVXY] 
Ginger Fresh Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B08KBVJ4XN] 
Barrel and Oak - Aluminum-Free Deodorant, Deodorant for Men, Essential Oil-Based Scent, 24-Hour Odor Protection, Cedar & Patchouli Blend, Gentle on Sensitive Skin (Mountain Sage, 2.7 oz, 2-Pack) 
$15.95  

Action: As a rule, I will always buy the first displayed product. On this page, it is B078GWRC1J. Now I will buy it.
Observation: OK.

Action: click[B078GWRC1J]
Observation: 
[Back to Search] 
[< Prev] 
scent [assorted scents][bright citrus][calming lavender][ginger fresh][simply non-scents]
size [travel set (4-pack)][3 ounce (pack of 1)][3-ounce (2-pack)]
Bright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
Price: $10.99 
Rating: N.A. 
[Description] 
[Features] 
[Reviews] 
[Buy Now]  

Action: click[bright citrus]
Observation: You have clicked bright citrus. 

Action: click[3 ounce (pack of 1)]
Observation: You have clicked 3 ounce (pack of 1). 

Action: click[Buy Now]
"""


def fetch_salient_info(task, succ):
    if succ: return ''
    query = re.findall(r"\[(.*?)\]", task)[0]
    if 'Buy[' in task or 'DetailMatch' in task:
        prod = query.split(',')[0]
        query = ' '.join(query.split(',')[1:])
    if 'Search[' in task:
        return f'Could not run search using query: {query}'
    elif 'SimpleMatch[' in task:
        return f'No simple and exact matching products found on the search page. Query: {query}'
    elif 'DetailMatch[' in task:
        return f'Product ID {prod} did not fully satisfy criteria: {query}'
    elif 'Buy[' in task:
        return f'Could not successfully buy product id {prod} for criteria: {query}'
    else:
        print('**Note**: Encountered an error in salient propagation')
        import pdb;
        pdb.set_trace()


agent_id = 0


class MainAgent:
    def __init__(self, record_path=None, model_name='gpt-3.5-turbo-0613', proxy='http://127.0.0.1:10809',
                 api_interval=5):
        self.completed_tasks = []
        self.task = None
        self.system_prompt = f'''You are an agent that navigates a shopping website. You are given the task of buying a product that satisfies a mentioned criteria. Your job is to come up with an abstract plan to successfully finish the task. You have access to the following modules to do specific tasks:
- Search[query]: Mention a query keywords to put into search bar. Brings you to the search page with only {page_len} most relevant products displayed.
- SimpleMatch[criteria]: Runs a superficial check based on product title and price to return a list products on the search page that exactly match the criteria. If information about any sub-criteria cannot be determined or do not match, the product is not included. If the criteria is very complex, it will likely fail and return an empty list. 
- DetailMatch[prod_id, criteria]: Tells you if a product with given prod_id, exactly matches your criteria (string).
- Buy[prod_id, criteria]: For the product, select the options such as size and color that best match the criteria.
To conduct search, design query based on the fact you will see the search page with only {page_len} top relevant items. There is no filter based on price in the search bar. Argument 'prod_id' denotes product id, it starts with B, and is an alphanumeric string of length 10.
'''
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.model_name = model_name
        self.proxy = proxy
        self.api_interval = api_interval
        self.record_path = record_path
        self.max_duplicate_times = 2

    def check_duplicate(self):
        if len(self.messages) <= 2 * self.max_duplicate_times:
            return False
        check_messages = [message['content'] for message in self.messages[-2:-2 - 2 * self.max_duplicate_times:-2]]
        all_equal = all(s == check_messages[0] for s in check_messages)
        return all_equal

    def add_user_prompt(self, prompt):
        if self.messages[-1]['role'] == "user":
            raise Exception("Role Error")
        self.messages.append({"role": "user", "content": prompt})

    def get_response(self, **kwargs):
        if self.check_duplicate():
            response = {"role": "assistant", "content": "<action>over()</action>"}
            self.messages = self.messages[:-2 * self.max_duplicate_times]
        else:
            response = chat_gpt(messages=self.messages, model_name=self.model_name, proxy=self.proxy,
                                sleep_time=self.api_interval, **kwargs)
        self.messages.append(response)
        if self.record_path is not None:
            with open(self.record_path, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, indent=4, ensure_ascii=False)
        return response

    def shorten_messages(self, prompt, idx=3):
        print(f"shorten_message: prompt={prompt}")
        if len(self.messages) > idx:
            self.messages[idx]['content'] = f"{prompt}"
        self.messages = self.messages[:idx + 1]

    def parse_actions(self, text):
        pattern = r'<action>(.*?)</action>'

        actions = re.findall(pattern, text)

        if len(actions) == 0:
            pattern2 = r'Action:\s*(.*?\])'
            actions = re.findall(pattern2, text)

        return actions


def execute(env, idx, task, past_info_prop={}, past_action_checkpoint=[], verbose=True):  # 执行动作，如果fail就自动reset
    info_prop = past_info_prop
    action_checkpoint = past_action_checkpoint
    if len(info_prop):
        if verbose: print('Loading ...', info_prop)
        if 'product' in info_prop.keys() and 'prod_id' in task:
            task = task.replace('prod_id', info_prop['product'][0])
        env, (obs, r, succ), info = executor(env, idx, task)

    else:
        env, (obs, r, succ), info = executor(env, idx, task)

    act_history = info['a_hist']

    if verbose:
        print(f"r={r}\nobs={obs}\nr={r}\nsucc={succ}\ninfo={info}")

    if succ or 'Buy[' in task:
        if succ:
            action_checkpoint.extend(act_history)
            info_prop['prev'] = task
        if succ and 'product' in info.keys():
            if 'product' not in info_prop.keys():
                info_prop['product'] = info['product']
            else:
                info_prop['product'] = info['product'] + info_prop['product']
        result_msg = f"Action: {task}\nResult: success."
        return env, r, succ, action_checkpoint, info_prop, result_msg

    # fail and can be modified
    info_prop['status'] = ''
    info_prop['status'] += fetch_salient_info(task, succ)
    info_prop['status'] += f'- Search results page: {obs}'
    if verbose:
        print(f"\nlogic:AND\ninfo_prop={info_prop}")

    prev_info = ''
    if 'status' in info_prop.keys():
        prev_info = info_prop['status']
    if verbose:
        print('Supplying prev info to planner: ', prev_info.split('\n')[0])

    query = re.findall(r"\[(.*?)\]", task)[0]

    if 'Buy[' in task or 'DetailMatch' in task: query = ' '.join(query.split(',')[1:])
    if 'Match[' in task:
        custom_task = 'Narrow down search for {}'.format(query)
    else:
        custom_task = 'Buy ' + query

    res = env.step(idx, 'reset')
    obs = res[0]

    # result_msg = f"Action: {task}\nResult: fail.\n Observation:{obs}\n Advice: try to {custom_task}"
    result_msg = f"Action: {task}\nResult: fail. {info_prop['status']}\nAdvice: the new goal is {custom_task}. Write an abstract plan to successfully complete the goal. Learn from and incorporate information from previous runs. Do not repeat previously successful or unsuccesful commands."

    return env, r, succ, action_checkpoint, info_prop, result_msg


def run_item(env, task, i, verbose=True, output_path=None):
    main_agent = MainAgent(record_path=f"{output_path}/main_agent.json", proxy=proxy, api_interval=10)
    plan_message = plan_prompt.format('-', task)
    main_agent.add_user_prompt(plan_message)
    response_message = main_agent.get_response(max_tokens=800)
    plan = response_message['content']
    first_action_prompt = f"""Please give me the action we should take now according to the plan. Surround the action with <action> and </action>. e.g. <action>Search[“3 ounce citrus deodorant sensitive skin”]</action>
Available Actions: [\'<action>Search[query]</action>\', \'<action>SimpleMatch[criteria]</action>\', \'<action>DetailMatch[prod_id, criteria]</action>\', \'<action>Buy[prod_id, criteria]</action>\', \'<action>over()</action>\']\nGive me your THOUGHT and ACTION. If the task is completed, call "<action>over()</action>"."""
    main_agent.add_user_prompt(first_action_prompt)
    response_message = main_agent.get_response()

    action_prompt = f"""Please give me the next action we should take. Surround the action with <action> and </action>. e.g. <action>Search[“3 ounce citrus deodorant sensitive skin”]</action>. You don’t have to strictly implement the plan, you can adjust the behavior appropriately based on the results of the action.
Available Actions: [\'<action>Search[query]</action>\', \'<action>SimpleMatch[criteria]</action>\', \'<action>DetailMatch[prod_id, criteria]</action>\', \'<action>Buy[prod_id, criteria]</action>\', \'<action>over()</action>\']\nGive me your THOUGHT and ACTION. If the task is completed, call "<action>over()</action>". Don't take the same actions as before."""

    max_iter = 10
    cur_iter = 0
    reward = 0
    action_history = []

    prev_act = []
    prev_obs = []

    try:
        while cur_iter < max_iter:
            cur_iter += 1
            actions = main_agent.parse_actions(response_message['content'])
            if len(actions) == 0:  # TODO: 探索是一个action好还是多个action好
                main_agent.add_user_prompt(f"""Please give me the action we should take now. Surround the action with <action> and </action>.
Available Actions: [\'<action>Search[query]</action>\', \'<action>SimpleMatch[criteria]</action>\', \'<action>DetailMatch[prod_id, criteria]</action>\', \'<action>Buy[prod_id, criteria]</action>\', \'<action>over()</action>\']""")
                response_message = main_agent.get_response()
                continue
            action = actions[0]

            if 'over' in action:
                return env, reward, action_history, plan

            env, r, _, a_hist, info_prob, result_msg = execute(env=env, idx=f'fixed_{i}', task=action,
                                                               past_action_checkpoint=action_history, past_info_prop={},
                                                               verbose=verbose)
            reward = max(reward, r)

            prev_act.append(action)
            print(f"prev_act={prev_act}")
            prev_obs.append(result_msg)

            # for action in actions:
            #     env, r, _, a_hist, info_prob, result_msg = execute(env=env, idx=f'fixed_{i}', task=action,
            #                                                        past_action_checkpoint=action_history, past_info_prop={},
            #                                                        verbose=verbose)
            #     reward = max(reward, r)
            #
            #     prev_act.append(action)
            #     print(f"prev_act={prev_act}")
            #     prev_obs.append(result_msg)
            summary = "The previous action and results are as follows:\n"
            for o in prev_obs:
                summary += f"{o}\n"
            main_agent.shorten_messages(summary + '\n' + action_prompt)
            response_message = main_agent.get_response()
    except openai.error.InvalidRequestError as e:
        print(f"openai request error:{e}")

    return env, reward, action_history, plan


def plan_and_run(env, idx, task: str, exec_prompt='', past_action_checkpoint=[], past_info_prop={}, depth=1, num_runs=0,
                 verbose=False, output_path='.',planner=None):
    global agent_id
    print(
        f"in plan_and_run\nenv={env}\nidx={idx},task={task}\npast_action={past_action_checkpoint}\npast info={past_info_prop}")

    plan_list = []
    init_res = env.step(idx, 'reset')
    if len(past_action_checkpoint):
        if verbose: print('Loaded Checkpoint: ', past_action_checkpoint)
        for act in past_action_checkpoint:
            (obs, reward, done) = env.step(idx, act)

    info_prop = past_info_prop
    # action_checkpoint = copy.deepcopy(past_action_checkpoint)
    action_checkpoint = past_action_checkpoint
    running_completion = ''
    succ = False
    try:
        logic = task['logic']
    except:
        logic = 'AND'

    planner = None

    if isinstance(task, str) and '[' in task:  # execute. If fail, decompose
        if verbose: print('Starting... ' + task, ' at depth ' + str(depth))
        if len(info_prop):
            if verbose: print('Loading ...', info_prop)
            if 'product' in info_prop.keys() and 'prod_id' in task:
                task = task.replace('prod_id', info_prop['product'][0])
            env, (obs, r, succ), info = executor(env, idx, task)

        else:
            env, (obs, r, succ), info = executor(env, idx, task)
        act_history = info['a_hist']

        if verbose:
            print(
                f"r={r}\nobs={obs}\nr={r}\nsucc={succ}"
                f"info={info}")
            print('Task ({}) at depth {}, Success: '.format(task, depth), succ)
        plan_list.append(task + ' at depth ' + str(depth) + ', success: ' + str(succ))
        if succ or depth >= max_depth or 'Buy[' in task:
            if succ:
                action_checkpoint.extend(act_history)
                info_prop['prev'] = task
            if succ and 'product' in info.keys():
                if 'product' not in info_prop.keys():
                    info_prop['product'] = info['product']
                else:
                    info_prop['product'] = info['product'] + info_prop['product']
            if verbose:
                print(
                    f"env={env}\nr={r}\nrunning_completion={running_completion}\naction_cp={action_checkpoint}\ndepth={depth}\n"
                    f"plan_list={plan_list}\nnum_runs={num_runs},info_prop={info_prop}")

            return env, r, succ, running_completion, action_checkpoint, depth, plan_list, num_runs, info_prop

        else:  # fail and can be decomposed more deeply

            if logic == 'AND':
                info_prop['status'] = ''
                info_prop['status'] += fetch_salient_info(task, succ)
                info_prop['status'] += f'- Search results page: {obs}'
                if verbose:
                    print(f"\nlogic:AND\ninfo_prop={info_prop}")

        prev_info = ''
        if 'status' in info_prop.keys():
            prev_info = info_prop['status']
        if verbose:
            print('Supplying prev info to planner: ', prev_info.split('\n')[0])

        query = re.findall(r"\[(.*?)\]", task)[0]

        if 'Buy[' in task or 'DetailMatch' in task: query = ' '.join(query.split(',')[1:])
        if 'Match[' in task:
            custom_task = 'Narrow down search for {}'.format(query)
        else:
            custom_task = 'Buy ' + query

        # plan = plan_llm(plan_prompt.format(f'\n{prev_info}', custom_task))

        agent_id += 1
        planner = MainAgent(record_path=f"{output_path}/main_agent_{agent_id}.json", proxy=proxy, api_interval=10)
        plan_message = plan_prompt.format(f'\n{prev_info}', custom_task)
        planner.add_user_prompt(plan_message)
        response_message = planner.get_response(max_tokens=800)
        plan = response_message['content']

        if verbose: print(); print(plan); print()
        plan_steps = plan_to_args(plan)
        if len(plan_steps['steps']) == 1:
            plan_steps = plan_steps['steps'][0]
            if type(plan_steps) == str: plan_steps = {'steps': [plan_steps]}
            if 'logic' not in plan_steps.keys():
                try:
                    logic = plan_steps['logic']
                except:
                    logic = "AND";
                    plan_steps['logic'] = logic
        depth += 1

    elif isinstance(task, str):  # Origin Goal
        # else:
        agent_id += 1
        planner = MainAgent(record_path=f"{output_path}/main_agent_{agent_id}.json", proxy=proxy, api_interval=10)
        plan_message = plan_prompt.format(f'-', task)
        planner.add_user_prompt(plan_message)
        response_message = planner.get_response(max_tokens=800)
        plan = response_message['content']
        plan_steps = plan_to_args(plan)
        if len(plan_steps['steps']) == 1:
            plan_steps = plan_steps['steps'][0]
            if type(plan_steps) == str: plan_steps = {'steps': [plan_steps]}
            if 'logic' not in plan_steps.keys():
                try:
                    logic = plan_steps['logic']
                except:
                    logic = "AND";
                    plan_steps['logic'] = logic

    else:  # task is not str, get logic. Then execute one by one.
        plan_steps = task
        try:
            logic = plan_steps['logic']
        except:
            logic = "AND";
            plan_steps['logic'] = logic

    if verbose: print(
        'Identified subtasks... ' + str(plan_steps['steps']) + ' at depth {}, logic: '.format(depth) + str(
            plan_steps['logic']))
    plan_list.append(str(plan_steps['steps']) + ' at depth ' + str(depth) + ' and logic ' + str(plan_steps['logic']))
    for sub_task in plan_steps['steps']:
        if verbose: print('At subtask: ' + str(sub_task))

        env, r, succ, completion, act_history, _, decomp_plans, num, info_prop = plan_and_run(env, idx, sub_task,
                                                                                              past_action_checkpoint=action_checkpoint,
                                                                                              past_info_prop=info_prop,
                                                                                              depth=depth,
                                                                                              verbose=verbose,
                                                                                              output_path=output_path)  # Fill in remaining args later

        plan_list.extend(decomp_plans)
        if plan_steps['logic'].lower() == 'or':
            if succ:
                if not set(act_history).issubset(action_checkpoint): action_checkpoint.extend(act_history)
                return env, r, succ, running_completion, action_checkpoint, depth, plan_list, num_runs, info_prop
        # If reached here you have succeeded. The logic is AND
        if succ:
            if not set(act_history).issubset(action_checkpoint): action_checkpoint.extend(act_history)

        if plan_steps['logic'].lower() == 'and' and not succ:  # otherwise next subtask
            if planner is None:
                return env, r, succ, running_completion, action_checkpoint, depth, plan_list, num_runs, info_prop
            # already fail, try to update the plan to make it success.
            elif planner is not None:
                update_prompt = f"""Failed during {sub_task}. Please write another plan. In each step of the plan mention which module (including arguments) that need to be called."""
                planner.add_user_prompt(update_prompt)
                response_message = planner.get_response(max_tokens=800)
                plan = response_message['content']
                if verbose: print(); print(plan); print()
                plan_steps = plan_to_args(plan)
                if len(plan_steps['steps']) == 1:
                    plan_steps = plan_steps['steps'][0]
                    if type(plan_steps) == str: plan_steps = {'steps': [plan_steps]}
                env, r, succ, completion, act_history, _, decomp_plans, num, info_prop = plan_and_run(env, idx,
                                                                                                      sub_task,
                                                                                                      past_action_checkpoint=action_checkpoint,
                                                                                                      past_info_prop=info_prop,
                                                                                                      depth=depth,
                                                                                                      verbose=verbose,
                                                                                                      output_path=output_path)

    print(f"env={env}\nr={r}\nrunning_completion={running_completion}\naction_cp={action_checkpoint}\ndepth={depth}\n"
          f"plan_list={plan_list}\nnum_runs={num_runs},info_prop={info_prop}")

    return env, r, succ, running_completion, action_checkpoint, depth, plan_list, num_runs, info_prop


def pipeline_run_episodes_TDAG(n=50, start_idx=100, verbose=True):
    rs = []
    cnt = 0
    logs = {}
    act_logs = {}
    score = 0
    sr = 0

    pbar = tqdm(range(start_idx, start_idx + n))
    pbar.set_postfix({'score': score, 'srate': sr})
    env = webshopEnv()
    for i in pbar:
        hist = []
        res = env.step(f'fixed_{i}', 'reset')
        obs = res[0]
        task = obs.split('Instruction:  \n')[-1].split('\n')[0]

        try:
            output_path = f"results/webshop/{LM}/{i}/"
            os.makedirs(output_path, exist_ok=True)
            env, r, a_hist, plan_hist = run_item(env=env, task=task, i=i, verbose=verbose, output_path=output_path)
            cnt += 1

        except AssertionError as e:
            print(f"AssertionError {e}")
            r = 0
            a_hist = []
            cnt += 1
            plan_hist = []
        except RetryError as e:
            print(f"RetryError {e}")
            r = 0
            a_hist = []
            cnt += 1
            plan_hist = []

        # add
        # except Exception as e:
        #     print(f"Exception {e}")
        #     r = 0
        #     a_hist = []
        #     cnt += 1
        #     plan_hist = []

        rs.append(r)
        logs[f'fixed_{i}'] = {}
        logs[f'fixed_{i}']['problem'] = task
        logs[f'fixed_{i}']['score'] = r
        logs[f'fixed_{i}']['success'] = r == 1
        logs[f'fixed_{i}']['action_history'] = a_hist
        logs[f'fixed_{i}']['plans'] = plan_hist

        score, sr, fr = sum(rs) / len(rs), len([_ for _ in rs if _ == 1]) / len(rs), cnt / len(
            rs)  # score, success rate, use of invalid actions
        pbar.set_postfix({'score': score, 'srate': sr})

    score, sr, fr = sum(rs) / len(rs), len([_ for _ in rs if _ == 1]) / n, cnt / n
    logs['overall'] = {'score': score, 'success_rate': sr, 'count': len(rs)}
    print(score, sr, fr)
    return rs, logs


def pipeline_run_episodes(n=50, start_idx=100, verbose=True):
    rs = []
    cnt = 0
    logs = {}
    act_logs = {}
    score = 0
    sr = 0

    pbar = tqdm(range(start_idx, start_idx + n))
    pbar.set_postfix({'score': score, 'srate': sr})
    env = webshopEnv()
    for i in pbar:
        hist = []
        res = env.step(f'fixed_{i}', 'reset')
        obs = res[0]
        task = obs.split('Instruction:  \n')[-1].split('\n')[0]

        try:
            # plan = plan_llm(plan_prompt.format(task, '-'))
            # plan = plan_llm(plan_prompt.format('-', task))
            # if verbose: print('Printing the plan'); print(plan); print()
            # plan_steps = plan_to_args(plan)
            # if len(plan_steps['steps']) == 1:
            #     plan_steps = plan_steps['steps'][0]
            # if verbose: print('Printing args to the main function.'); print(plan_steps); print()
            # env, r, _, _, a_hist, depth, plan_hist, _, _ = plan_and_run(env=env, idx=f'fixed_{i}', task=plan_steps,
            #                                                             past_action_checkpoint=[], past_info_prop={},
            #                                                             depth=1, verbose=verbose)
            global agent_id
            agent_id = 0
            output_path = f"results/webshop/{LM}/{i}"
            os.makedirs(output_path, exist_ok=True)
            env, r, _, _, a_hist, depth, plan_hist, _, _ = plan_and_run(env=env, idx=f'fixed_{i}', task=task,
                                                                        past_action_checkpoint=[], past_info_prop={},
                                                                        depth=0, verbose=verbose,
                                                                        output_path=output_path)
        except AssertionError as e:
            print(f"AssertionError {e}")
            r = 0
            a_hist = []
            cnt += 1
            plan_hist = []
        except RetryError as e:
            print(f"RetryError {e}")
            r = 0
            a_hist = []
            cnt += 1
            plan_hist = []
        # add
        # except Exception as e:
        #     print(f"Exception {e}")
        #     r = 0
        #     a_hist = []
        #     cnt += 1
        #     plan_hist = []

        rs.append(r)
        logs[f'fixed_{i}'] = {}
        logs[f'fixed_{i}']['problem'] = task
        logs[f'fixed_{i}']['score'] = r
        logs[f'fixed_{i}']['success'] = r == 1
        logs[f'fixed_{i}']['action_history'] = a_hist
        logs[f'fixed_{i}']['plans'] = plan_hist

        score, sr, fr = sum(rs) / len(rs), len([_ for _ in rs if _ == 1]) / len(rs), cnt / len(
            rs)  # score, success rate, use of invalid actions
        pbar.set_postfix({'score': score, 'srate': sr})

    score, sr, fr = sum(rs) / len(rs), len([_ for _ in rs if _ == 1]) / n, cnt / n
    logs['overall'] = {'score': score, 'success_rate': sr, 'count': len(rs)}
    print(score, sr, fr)
    return rs, logs


num_sess = 100
start_idx = 0
os.makedirs(f"results/webshop/{LM}/", exist_ok=True)
res, logs = pipeline_run_episodes_TDAG(num_sess, start_idx=start_idx, verbose=True)
json.dump(logs, open(f'results/webshop/TDAG_dev1_{start_idx}_{num_sess}.json', "w+"), indent=4)
