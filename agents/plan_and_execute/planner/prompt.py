from agents.main_agent.prompt import subtask_format, TASK_DESCRIPTION
SYSTEM_PROMPT = f'''You are a helpful assistant to make travel plans for Bob.

EXTERNAL RESOURCES:
1. A database containing information about train tickets, attractions, and city transportation.
2. A python notebook to execute python code for numerical operations and planning. 

{TASK_DESCRIPTION}

--- Your Workflow ---
1. You will first be given a task.
2. You should understand the task and devise a plan to complete the task. This plan will contain a series of subtasks that need to be completed.

PLAN AND SUBTASK:
If the task cannot be easily solved directly or requires the use of external resources, please assign it to another agent to complete (such as "find the cheapest train from Beijing to Shanghai in 2023-7-1"), otherwise you can complete it yourself. You may need to wait for results from other agents before proceeding to the next step of the task. If you need help from other agents, please clearly describe the task objectives, background, and precautions of the subtask. 
A subtask-structure has the following json component and surrounded with <subtask></subtask> as follows:
{subtask_format}

'''

USER_FIRST = '''Task Requirements:
{{task}}
Come up with an abstract plan to perform this task in a couple of steps. Give me the subtasks between <subtask> and </subtask>.'''

USER_PROMPT = """Subtask Results:\n{{observation}}
"""
from agents.main_agent.prompt import USER_OVER_PROMPT as main_user_over_prompt

USER_OVER_PROMPT = USER_PROMPT + main_user_over_prompt

RESULT_PROMPT=USER_PROMPT+'''Current task:
{{task}}
Give me the final result of current task. Surround the result between <result> and </result>'''

EXAMPLE_MESSAGES = [{'role': 'system', 'name': 'example_user',
                     'content': '''Task Requirements: Bob is in Shanghai and going to travel in several cities, please make a ticket purchase plan and travel sequence for him.The demands are as follows:
1. visit ['Beijing']. The order doesn't matter and he needs to return to Shanghai finally.
2. He is free to travel from 2023.7.1 to 2023.7.20. The budget for transportation is 1000.0 CNY.
3. Play at least 3 days in Beijing.
4. If you arrive in a city before 12:00 noon, that day can be counted as a day of play. If it's past 12 o'clock, it doesn't count as a day.
5. On the basis of completing the above conditions (especially the budget), spend as little time as possible.
'''},
                    {'role': 'system', 'name': 'example_assistant', 'content':
                        '''Based on the requirements, we can know that Bob need to go to Beijing from Shanghai, stay in Beijing for 3 days and then go to Shanghai from Beijing.
Given the task, the first step is to find available train tickets that fit Bob's schedule and budget.
<subtask>
{
"subtask_name": "find_available_train_tickets",
"goal": "Find train tickets from Shanghai to Beijing and back to Shanghai that fit within the travel dates, budget, and allow for at least 3 full days of play in Beijing. If the arrival is before 12:00 noon, it counts as a day of play.",
"criticism": "Must ensure that the total cost of the round trip tickets does not exceed the budget of 1000.0 CNY and that the timings allow for at least 3 full days in Beijing for visit. So you need to allow time between train rides(arrival in a city and departure from the city). For each ticket, you must give me the ticket number, origin, destination, departure time, arrival time and the price.",
"milestones": ["Identify a suitable train from Shanghai to Beijing.", "Identify a return train from Beijing to Shanghai ensuring at least 3 days in Beijing before departing.", "Ensure the total cost of both tickets is within the budget of 1000.0 CNY."]
}
</subtask>
Then we can get the final plan consists of go_to_city and stay_in.
<subtask>
{
"subtask_name": "get the final plan",
"goal": "Formulate a travel plan for Bob's trip from Shanghai to Beijing and back, ensuring it fits within his budget and time constraints, including at least 3 full days in Beijing.",
"criticism": "The plan must be concise, focusing on efficient travel and stay arrangements while adhering to the budget and time constraints.",
"milestones": ["Include suitable train journeys within the budget.","Plan at least 3 full days in Beijing.","Ensure the overall plan fits within the specified dates and budget."],
"result_format": "A schedule consisting with multiple <plan>go_to_place(...)</plan> and <plan>visit(...)</plan>.    1.go_to_place(origin:str,destination:str,departure_time,arrival_time): go to destination from origin.     2.visit(place:str,begin_time,end_time): visit somewhere from begin_time to end_time. The time should be expressed\
 as %Y-%m-%d %H:%M, e.g. 2023-07-02 16:00."
}
</subtask>
'''}]

EXAMPLE_MESSAGES_2 = [{'role': 'system', 'name': 'example_user',
                       'content': '''Task Requirements: Bob is going to play in Wuhan, please make a visit plan for him.The demands are as follows:\n1. He lives in Wuhan Railway Hotel. He needs to visit ['Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', 'Baotong Temple'] and the order can be decided by you.\n2. 2 days(2023-07-06 00:00 ~ 2023-07-08 00:00) for this trip. He can only go out to play from 7:00 to 22:00 every day, and needs to go back to the hotel to rest at other times.\n3. Visit Han Show for 150 minutes, Hubu Alley for 180 minutes, Yellow Crane Tower for 240 minutes, Tan Hua Lin for 240 minutes, Baotong Temple for 300 minutes.\n4. Ignore the opening hours of attractions, assuming they are open all day\n5. On the basis of completing the above conditions, spend as little time as possible (when He visits all of the above places, the earlier, the better) so you should carefully consider the visiting sequence and timing.'''},
                      {'role': 'system', 'name': 'example_assistant', 'content':
                          '''To create an efficient travel plan for Bob, our first subtask is to determine the optimal sequence of visits to the five specified locations in Wuhan. This sequence should minimize the overall travel time between these attractions.
Subtask 1: Get Visit Sequence In Wuhan
<subtask>
{
"subtask_name": "Optimal Visit Sequence In Wuhan",
"goal": "Find the most efficient sequence for visiting 'Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', and 'Baotong Temple' in Wuhan. This involves determining the order that minimizes travel time between these attractions.",
"criticism": "The challenge is in accurately estimating travel times between different locations without real-time data. The chosen sequence might not be the absolute best due to unforeseen circumstances like traffic conditions.",
"milestones": [
"Determine the locations of 'Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', and 'Baotong Temple'.",
"Estimate the travel time between each pair of attractions.",
"Use an algorithm or heuristic to find the sequence of visits that minimizes the total travel time.",
"Confirm the final sequence for the visits."
],
"result_format": "a list of spots to visit"
}</subtask>

Subtask 2: creating a detailed itinerary for Bob's visit to Wuhan, incorporating the optimal sequence of attractions based on the result of subtask 1.
<subtask>
{
"subtask_name": "Arranging Wuhan Visits",
"goal": "Create a detailed travel and visit plan for Bob in Wuhan, including travel to and from 'Tan Hua Lin', 'Baotong Temple', 'Han Show', 'Hubu Alley', and 'Yellow Crane Tower', as well as the duration of each visit. This requires calculating travel times between each location and the hotel, and scheduling visits within the specified time frame.",
"criticism": "The plan may face challenges due to the lack of real-time traffic data and the need to estimate travel times.",
"milestones": [
"Retrieve estimated travel times between Wuhan Railway Hotel and each attraction, and between each pair of attractions, from the database.",
"Calculate the time needed for each segment of the trip, including travel and visit durations.",
"Schedule each activity (travel and visit) within the allowed time frame (7:00 to 22:00 each day).",
"Ensure the total visit time at each attraction meets the specified duration.",
"Compile the final itinerary in a coherent and chronological order."
],
"result_format": "A schedule consisting with multiple <plan>go_to_place(origin,destination,departure_time,arrival_time)</plan> and <plan>visit(place,begin_time,end_time)</plan> "
}</subtask>
'''}]

EXAMPLE_MESSAGES_3 = [{'role': 'system', 'name': 'example_user',
                       'content': '''Task Requirements: Bob is going to visit some spots across cities, please make a visit plan for him, including inter-city transportation, intra-city transportation, and visit time for each spot.The demands are as follows:\n1. He now lives in Wuhan Railway Hotel in Wuhan. In Guangzhou, he needs to visit Canton Tower for 150 minutes, Baiyun Mountain for 210 minutes.In Hangzhou, he needs to visit China National Tea Museum for 120 minutes, Quaint Water Towns for 150 minutes, Lingyin Temple for 240 minutes, West Lake for 180 minutes. And the order can be decided by you.\n2. 5 days (2023-07-9 07:00 ~ 2023-07-14 00:00) for this trip.\n3. Ignore the opening hours of attractions, assuming they are open all day\n4. On the basis of completing the above conditions (especially the time limit), spend as little money as possible.
'''},
                      {'role': 'system', 'name': 'example_assistant', 'content':
                          '''Based on the requirements, Bob need to visit ["Guanzhou","Hangzhou"] and now he is in Wuhan. A simple way is to first find a random order of the cities. The order of visiting cities can be [Guangzhou, Hangzhou] according to the location. So he needs to: 1. go to Guangzhou from Wuhan. 2. visit apots in Wuhan. 3.go to Hangzhou from Wuhan. 4.visit Hangzhou. Then the task is completed.
Subtask 1: get train ticket information from Wuhan to Guangzhou
<subtask>
{
"subtask_name": "Find available train tickets from Wuhan to Guangzhou",
"goal": "Find available train tickets from Wuhan to Guangzhou",
"criticism": "Consider the departure time and the price.",
"milestones": ["Get the ticket number, departure time, arrival time and price"],
"result_format": "the information of the ticket: origin_city:str,destination_city:str,departure_time,arrival_time,ticket_number"
}
</subtask>
Subtask 2: Arranging Intra-city Transportation and Visits in Guangzhou
<subtask>
{
"subtask_name": "Arrange Guangzhou Visits",
"goal": "Organize intra-city transportation in Guangzhou to visit Canton Tower and Baiyun Mountain, ensuring Bob spends the required time at each location.",
"criticism": "Time management is crucial to ensure Bob spends the required time at each attraction. Also, consider the time spent in traffic from one place to another.",
"milestones": ["Decide visit order", "Calculate travel time between spots and the time for visiting", "Arrange transportation and visit schedule starting from Guangzhou Railway Hotel,including go_to_place() and visit(). The begin time is determined by the results of the previous subtasks."],
"result_format": "A schedule consisting with multiple <plan>go_to_place(...)</plan> and <plan>visit(...)</plan>.    1.go_to_place(origin:str,destination:str,departure_time,arrival_time): go to destination from origin.     2.visit(place:str,begin_time,end_time): visit somewhere from begin_time to end_time. The time should be expressed\
 as %Y-%m-%d %H:%M, e.g. 2023-07-02 16:00."
}
</subtask>

Subtask 3: Finding Transportation from Guangzhou to Hangzhou (to be modified based on the execution results of the previous subtasks.)
<subtask>
{
"subtask_name": "Find Guangzhou-Hangzhou Transportation",
"goal": "Find the most cost-effective transportation option from Guangzhou to Hangzhou that fits within the travel time frame.",
"criticism": "Consider the time taken for travel and any layovers, ensuring Bob has enough time to visit all attractions in Hangzhou within the specified days.",
"milestones": ["Find available transportation options", "Select the most cost-effective option", "Ensure arrival in Hangzhou allows enough time for visiting all planned attractions"],
"result_format": "the information of the ticket: origin_city:str,destination_city:str,departure_time,arrival_time,ticket_number"
}
</subtask>

Subtask 4: Arranging Intra-city Transportation and Visits in Hangzhou (to be modified based on the execution results of the previous subtasks.)
<subtask>
{
"subtask_name": "Arrange Hangzhou Visits",
"goal": "Organize intra-city transportation in Hangzhou to visit China National Tea Museum, Quaint Water Towns, Lingyin Temple, and West Lake, ensuring Bob spends the required time at each location.",
"criticism": "Time management is crucial to ensure Bob spends the required time at each attraction. Also, consider the time spent in traffic from one place to another.",
"milestones": ["Decide visit order", "Calculate visit and travel time between spots", "Arrange transportation and visit schedule starting from Hangzhou Railway Hotel. The begin time is determined by the results of the previous subtasks."],
"result_format": "A schedule consisting with multiple <plan>go_to_place(...)</plan> and <plan>visit(...)</plan>.    1.go_to_place(origin:str,destination:str,departure_time,arrival_time): go to destination from origin.     2.visit(place:str,begin_time,end_time): visit somewhere from begin_time to end_time. The time should be expressed\
 as %Y-%m-%d %H:%M, e.g. 2023-07-02 16:00."
}
'''}
]
