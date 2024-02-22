from agents.agent_generator.prompt import ORIGINAL_DOCUMENT
from agents.main_agent.prompt import TASK_DESCRIPTION

SYSTEM_PROMPT = f'''You are an autonomous intelligent agent tasked with making travel plans for Bob. To be successful, it is very important to follow the following rules:
1. You should only issue one action at a time.
2. You should reason step by step and then issue the next action.
3. Your response should be formatted as follows:
THOUGHT: the thought process to achieve the goal, including the subtask to be handled.
ACTION: the action you call to get information or submit the task.

EXTERNAL RESOURCES:
1. A database containing information about train tickets, attractions, and city transportation.
2. A python notebook to execute python code for numerical operations and planning. 

{TASK_DESCRIPTION}

--- Your Workflow ---
1. You will first be given a task.
2. Then you will start to solve it step by step. You need to give your ideas until you need to use external tools to obtain information or calculations, and then call an action and waif for the result.
3. Finally, call over() to indicate task completion. After the content in task requirements is completed, call over() immediately without making unnecessary planning.

--- Available Actions ---
{ORIGINAL_DOCUMENT}

<action>over()</action>
When you think the task is completed, call "<action>over()</action>"

Now you will be given a task. Start planning and give me an action.
'''

USER_FIRST = '''Task Requirements:
{{task}}
Start your planning until you need to call an action. Give me the THOUGHT and ACTION.'''

from agents.main_agent.prompt import USER_PROMPT as main_user_prompt

USER_PROMPT = main_user_prompt

# USER_PROMPT = """Action Result:\n{{observation}}
# Available Actions: {{action_space}}
# Continue your planning until you need an action. If the task is completed, call "<action>over()</action>".
# """

from agents.main_agent.prompt import USER_OVER_PROMPT as main_user_over_prompt

USER_OVER_PROMPT = main_user_over_prompt

EXAMPLE_MESSAGES_1 = [{'role': 'system', 'name': 'example_user',
                       'content': '''Task Requirements: Bob is in Shanghai and going to travel in several cities, please make a ticket purchase plan and travel sequence for him.The demands are as follows:
1. visit ['Beijing']. The order doesn't matter and he needs to return to Shanghai finally.
2. He is free to travel from 2023.7.1 to 2023.7.20. The budget for transportation is 1000.0 CNY.
3. Play at least 3 days in Beijing.
4. If you arrive in a city before 12:00 noon, that day can be counted as a day of play. If it's past 12 o'clock, it doesn't count as a day.5. On the basis of completing the above conditions (especially the budget), spend as little time as possible.\n
'''},
                      {'role': 'system', 'name': 'example_assistant', 'content':
                          '''THOUGHT:
To fulfill Bob's travel objectives, I need to consider the following points:
Bob needs to visit Beijing from Shanghai and then return to Shanghai.
He has a window between 2023-07-01 to 2023-07-20 to make this trip.
The budget for the entire journey is 1000.0 CNY.
He wants to spend at least 3 days in Beijing.
If he arrives in a city before 12:00 noon, the day can be counted as a play day. Otherwise, it doesn't count.
Firstly, let's find out the available train options from Shanghai to Beijing and back. I'll query the railway database to find trains that suit Bob's schedule and budget.
ACTION:
I'll start by executing an SQL query to fetch 5 train options from Shanghai to Beijing, departing on or after 2023-07-01.
<action>
execute_sql(\'\'\'
SELECT * FROM railway
WHERE origin = 'Shanghai'
  AND destination = 'Beijing'
  AND DATE(departure_time) >= '2023-07-01'
  LIMIT 5;
\'\'\')
</action>'''},
                      {'role': 'system', 'name': 'example_user',
                       'content': '''Action Result:\n{\'query\': "\nSELECT * FROM railway\nWHERE origin = \'Shanghai\'\n  AND destination = \'Beijing\'\n  AND DATE(departure_time) >= \'2023-07-01\'\n  LIMIT 5;", \'result\': [[\'D1003\', \'Shanghai\', \'Beijing\', \'2023-07-01 22:54\', \'2023-07-02 09:29\', 635, 300.0], [\'G1008\', \'Shanghai\', \'Beijing\', \'2023-07-01 06:29\', \'2023-07-01 13:19\', 410, 580.0], [\'G1013\', \'Shanghai\', \'Beijing\', \'2023-07-01 10:32\', \'2023-07-01 17:11\', 399, 580.0], [\'G1016\', \'Shanghai\', \'Beijing\', \'2023-07-01 17:05\', \'2023-07-01 20:27\', 202, 680.0], [\'D1325\', \'Shanghai\', \'Beijing\', \'2023-07-02 18:41\', \'2023-07-03 08:40\', 839, 300.0]], \'error\': None}\nAvailable Actions: [\'<action>execute_sql(statement:string)</action>\', \'<action>execute_python(code:string)</action>\', \'<action>over()</action>\']\nContinue your planning until you need an action. If the task is completed, call "<action>over()</action>".\n'''},
                      {'role': 'system', 'name': 'example_assistant', 'content': '''THOUGHT:
I've received a list of train options from Shanghai to Beijing. We can choose the cheapest ticket because we need to spend as little money as possible and have enough time. So the ticket is:
Train D1003:
    Departure: 2023-07-01 22:54
    Arrival: 2023-07-02 09:29
    Duration: 635 minutes
    Price: 300.0 CNY
Since Bob has a budget of 1000 CNY and wants to spend at least 3 days in Beijing, I'll keep in mind the following while selecting the train:
1.The departure time of the train must be after 2023-07-05 09:29.
2.The price of the ticket must be less than 1000-300=700 CNY。
ACTION:
Let's query the database for train options from Beijing back to Shanghai departing after 2023-07-04 (considering at least 3 days in Beijing) and the price must below 700 CNY.
<action>execute_sql(\'\'\'
SELECT * FROM railway
WHERE origin = 'Beijing'
AND destination = 'Shanghai'
AND DATE(departure_time) >= '2023-07-05'
AND price <= 700.0
LIMIT 5;
\'\'\')
</action>
'''},
                      {'role': 'system', 'name': 'example_user',
                       'content': '''OBSERVATION:\n[{'query': "\nSELECT * FROM railway\nWHERE origin = 'Shanghai'\n  AND destination = 'Beijing'\n  AND DATE(departure_time) >= '2023-07-01'\n  LIMIT 5;", 'result': [['D1003', 'Shanghai', 'Beijing', '2023-07-01 22:54', '2023-07-02 09:29', 635, 300.0], ['G1008', 'Shanghai', 'Beijing', '2023-07-01 06:29', '2023-07-01 13:19', 410, 580.0], ['G1013', 'Shanghai', 'Beijing', '2023-07-01 10:32', '2023-07-01 17:11', 399, 580.0], ['G1016', 'Shanghai', 'Beijing', '2023-07-01 17:05', '2023-07-01 20:27', 202, 680.0], ['D1325', 'Shanghai', 'Beijing', '2023-07-02 18:41', '2023-07-03 08:40', 839, 300.0]], 'error': None}]\n'''},
                      {'role': 'system', 'name': 'example_assistant', 'content': '''THOUGHT:
I have received the train options for the journey from Beijing back to Shanghai. There are several options available that fit within Bob's budget and schedule. I should opt for the one that allows Bob to spend at least 3 days in Beijing while also being cost-effective.
Given that Bob's departure from Shanghai to Beijing is on 2023-07-01 at 22:54 and he will arrive in Beijing on 2023-07-02 at 09:29, Bob can spend the 2nd, 3rd, and 4th of July as his play days in Beijing. So he should aim to depart from Beijing on the 5th of July or later.
For the sake of budget and minimum stay, the best option would be to opt for the D2582 train for 300.0 CNY, which departs on 2023-07-06. This ensures he can play for 3 days in Beijing while also keeping his total expenditure to 600.0 CNY, well under the budget of 1000.0 CNY.
Travel Plan for Bob:

Depart from Shanghai to Beijing on 2023-07-01 at 22:54 via train D1003. Arrive in Beijing on 2023-07-02 at 09:29.
Duration: 635 minutes
Price: 300.0 CNY
Play in Beijing on 2023-07-02, 2023-07-03, and 2023-07-04.
Depart from Beijing to Shanghai on 2023-07-06 at 09:16 via train D2582. Arrive in Shanghai on 2023-07-06 at 22:53.
Duration: 817 minutes
Price: 300.0 CNY
Total expenditure: 600.0 CNY (within budget of 1000.0 CNY)
ACTION:<action>over()</action>
'''}
                      ]

EXAMPLE_MESSAGES_2 = [
    {'role': 'system', 'name': 'example_user',
     'content': '''Bob is going to play in Wuhan, please make a visit plan for him.The demands are as follows:
1. He lives in Wuhan Railway Hotel. He needs to visit ['Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', 'Baotong Temple'] and the order can be decided by you.
2. 2 days(2023-07-06 00:00 ~ 2023-07-08 00:00) for this trip. He can only go out to play from 7:00 to 22:00 every day, and needs to go back to the hotel to rest at other times.
3. Visit Han Show for 150 minutes, Hubu Alley for 180 minutes, Yellow Crane Tower for 240 minutes, Tan Hua Lin for 240 minutes, Baotong Temple for 300 minutes.
4. Ignore the opening hours of attractions, assuming they are open all day
5. On the basis of completing the above conditions, spend as little time as possible (when He visits all of the above places, the earlier, the better) so you should carefully consider the visiting sequence and timing.'''},

    {'role': 'system', 'name': 'example_assistant', 'content':
        '''THOUGHT: 
To create an efficient travel plan for Bob in Wuhan, the first step is to gather information about the travel times between the hotel and each of the attractions, as well as between the attractions themselves. This will help in determining the most time-efficient sequence of visits. The attractions Bob needs to visit are Han Show, Hubu Alley, Yellow Crane Tower, Tan Hua Lin, and Baotong Temple.
ACTION: I will retrieve the travel duration data between these locations within Wuhan to start forming the travel sequence.

<action>execute_sql(\'\'\'
SELECT origin, destination, duration FROM in_city_transport
WHERE city = 'Wuhan' AND
(origin IN ('Wuhan Railway Hotel', 'Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', 'Baotong Temple') AND
destination IN ('Wuhan Railway Hotel', 'Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', 'Baotong Temple'));
\'\'\')</action>'''},
    {
        "role": "system",
        "name": "example_user",
        "content": "Action Result:\n{\"query\": \"\nSELECT origin, destination, duration FROM in_city_transport\nWHERE city = 'Wuhan' AND\n(origin IN ('Wuhan Railway Hotel', 'Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', 'Baotong Temple') AND\ndestination IN ('Wuhan Railway Hotel', 'Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', 'Baotong Temple'));\n\", \"result\": [[\"Han Show\", \"Yellow Crane Tower\", 67], [\"Yellow Crane Tower\", \"Han Show\", 67], [\"Baotong Temple\", \"Yellow Crane Tower\", 52], [\"Yellow Crane Tower\", \"Baotong Temple\", 52], [\"Baotong Temple\", \"Han Show\", 71], [\"Han Show\", \"Baotong Temple\", 71], [\"Tan Hua Lin\", \"Yellow Crane Tower\", 55], [\"Yellow Crane Tower\", \"Tan Hua Lin\", 55], [\"Tan Hua Lin\", \"Han Show\", 33], [\"Han Show\", \"Tan Hua Lin\", 33], [\"Tan Hua Lin\", \"Baotong Temple\", 47], [\"Baotong Temple\", \"Tan Hua Lin\", 47], [\"Hubu Alley\", \"Yellow Crane Tower\", 23], [\"Yellow Crane Tower\", \"Hubu Alley\", 23], [\"Hubu Alley\", \"Han Show\", 50], [\"Han Show\", \"Hubu Alley\", 50], [\"Hubu Alley\", \"Baotong Temple\", 75], [\"Baotong Temple\", \"Hubu Alley\", 75], [\"Hubu Alley\", \"Tan Hua Lin\", 56], [\"Tan Hua Lin\", \"Hubu Alley\", 56], [\"Wuhan Railway Hotel\", \"Yellow Crane Tower\", 72], [\"Yellow Crane Tower\", \"Wuhan Railway Hotel\", 72], [\"Wuhan Railway Hotel\", \"Han Show\", 42], [\"Han Show\", \"Wuhan Railway Hotel\", 42], [\"Wuhan Railway Hotel\", \"Baotong Temple\", 46], [\"Baotong Temple\", \"Wuhan Railway Hotel\", 46], [\"Wuhan Railway Hotel\", \"Tan Hua Lin\", 20], [\"Tan Hua Lin\", \"Wuhan Railway Hotel\", 20], [\"Wuhan Railway Hotel\", \"Hubu Alley\", 54], [\"Hubu Alley\", \"Wuhan Railway Hotel\", 54]], \"error\": \"\"}\nAvailable Actions: ['<action>execute_sql(statement:string)</action>', '<action>execute_python(code:string)</action>', '<action>over()</action>']\nContinue your planning until you need an action. If the task is completed, call \"<action>over()</action>\"."
    }
]

EXAMPLE_MESSAGES_3 = [
    {'role': 'system', 'name': 'example_user',
     'content': '''Task Requirements: Bob is going to visit some spots across cities, please make a visit plan for him, including inter-city transportation, intra-city transportation, and visit time for each spot.The demands are as follows:\n1. He now lives in Wuhan Railway Hotel in Wuhan. In Guangzhou, he needs to visit Canton Tower for 150 minutes, Baiyun Mountain for 210 minutes.In Hangzhou, he needs to visit China National Tea Museum for 120 minutes, Quaint Water Towns for 150 minutes, Lingyin Temple for 240 minutes, West Lake for 180 minutes. And the order can be decided by you.\n2. 5 days (2023-07-9 07:00 ~ 2023-07-14 00:00) for this trip.\n3. Ignore the opening hours of attractions, assuming they are open all day\n4. On the basis of completing the above conditions (especially the time limit), spend as little money as possible.
'''},

    {'role': 'system', 'name': 'example_assistant', 'content':
        '''THOUGHT: Based on the requirements, Bob need to visit ["Guanzhou","Hangzhou"] and now he is in Wuhan. A simple way is to first find a random order of the cities. The order of visiting cities can be [Guangzhou, Hangzhou] according to the location. So he first needs to go to Guangzhou from Wuhan. We can first confirm his ticket to Wuhan.
To begin planning Bob's trip, I need to find the most suitable train ticket for him to travel from Wuhan to Guangzhou. This involves checking the railway database for available train tickets, considering factors like departure times and prices to ensure his journey fits within the specified time frame and budget constraints. Once I have this information, I can decide on the best ticket option and proceed with the next steps of the trip planning.
ACTION: To find train options from Wuhan to Guangzhou, I will query the railway database.
<action>execute_sql(\'\'\'
SELECT * FROM railway
WHERE origin = 'Wuhan'
AND destination = 'Guangzhou'
AND DATE(departure_time) >= '2023-07-09'
LIMIT 5;\'\'\')</action>'''},
    {'role': 'system', 'name': 'example_user',
     'content': """Action Result:\n{\'query\': "\nSELECT * FROM railway\nWHERE origin = \'Wuhan\'\nAND destination = \'Guangzhou\'\nAND DATE(departure_time) >= \'2023-07-09\'\nLIMIT 5;", \'result\': [[\'G3819\', \'Wuhan\', \'Guangzhou\', \'2023-07-09 14:49:00\', \'2023-07-09 19:28:00\', 279, 443.0], [\'G3823\', \'Wuhan\', \'Guangzhou\', \'2023-07-09 18:34:00\', \'2023-07-09 23:28:00\', 294, 443.0], [\'K3830\', \'Wuhan\', \'Guangzhou\', \'2023-07-09 13:41:00\', \'2023-07-09 23:49:00\', 608, 148.0], [\'G4131\', \'Wuhan\', \'Guangzhou\', \'2023-07-10 12:14:00\', \'2023-07-10 17:16:00\', 302, 443.0], [\'K4136\', \'Wuhan\', \'Guangzhou\', \'2023-07-10 18:51:00\', \'2023-07-11 06:45:00\', 714, 148.0]], \'error\': \'\'}\nAvailable Actions: [\'<action>execute_sql(statement:string)</action>\', \'<action>execute_python(code:string)</action>\', \'<action>over()</action>\']\nContinue your planning until you need an action. If the task is completed, call "<action>over()</action>"."""
     }
]
