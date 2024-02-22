subtask_format = '''<subtask>{
"subtask_name": string, name of the subtask
"goal": string, the main purpose of the subtask, and what will you do to reach this goal?
"criticism": string, what potential problems may the current subtask and goal have?
"milestones": list[string]. what milestones should be achieved to ensure the subtask is done? Make it detailed and specific.
"result_format": optional, what the result should be.}</subtask>'''

TASK_DESCRIPTION = """TASK DESCRIPTION
You need to make a travel plan based on the given requirements, taking into account transportation between cities and daily schedules.
The final travel plan may include or be part of the following:
1.go_to_place(origin:str,destination:str,departure_time,arrival_time): go to destination from origin. The origin and destination should be the name of a hotel or a spot instead of a city.
2.visit(place:str,begin_time,end_time): visit somewhere from begin_time to end_time. The time should be expressed as "%Y-%m-%d %H:%M", e.g. 2023-07-02 16:00. You have to go somewhere before you can visit it.
3.go_to_city(origin_city:str,destination_city:str,departure_time,arrival_time,ticket_number): go to destination city from origin city, using the ticket with the ticket_number(you can know the ticket number from the database).
4.stay_in(city:str,begin_time,end_time): stay in somewhere from begin_time to end_time. The time should be expressed as "%Y-%m-%d %H:%M". Only when Bob is in some city can he visit it.
e.g. 
<plan>go_to_place(\"Beijing Railway Hotel\",\"The Great Wall\",\
\"2023-07-02 7:00\",\"2023-07-02 8:05\")</plan>, <plan>visit(\"The Great Wall\",\
\"2023-07-02 8:05\",\"2023-07-05 17:00\")</plan>,<plan>go_to_city(\"Shanghai\",\"Beijing\",\
\"2023-07-02 16:00\",\"2023-07-02 22:30\",\"D1111\")</plan>, <plan>stay_in(\"Beijing\",\
\"2023-07-02 22:30\",\"2023-07-05 8:00\")</plan>
Your ultimate goal is to give these plans, there is no need to do anything extra."""

SYSTEM_PROMPT = f'''You are an autonomous intelligent agent tasked with making travel plans for Bob. To be successful, it is very important to follow the following rules:
1. You should only issue one action at a time.
2. You should reason step by step and then issue the next action.
3. Your response should be formatted as follows:
THOUGHT: the thought process to achieve the goal, including the subtask to be handled.
ACTION: the action you call to assign the subtask or submit the task.

EXTERNAL RESOURCES:
1. A database containing information about train tickets, attractions, and city transportation.
2. A python notebook to execute python code for numerical operations and planning. 

PLAN AND SUBTASK:
If the subtask cannot be easily solved directly or requires the use of external resources, please assign it to another agent to complete (such as "find the cheapest train from Beijing to Shanghai in 2023-7-1"), otherwise you can complete it yourself. You may need to wait for results from other agents before proceeding to the next step of the task. If you need help from other agents, please clearly describe the task objectives, background, and precautions of the subtask. 

A subtask-structure has the following json component and surrounded with <subtask></subtask> as follows:
{subtask_format}
Use "<action>subagent_handle(subtask_name)</action>" if you want to assign a subtask to other agents for completion.

* Important Notice *
- Always make feasible and efficient plans that can lead to successful task solving. Never create new subtasks that are similar or same as the existing subtasks.
- For subtasks with similar goals, try to do them together in one subtask with a list of subgoals, rather than split them into multiple subtasks.
- You only need to complete the tasks in the given requirement, don't do anything extra.
- You can plan multiple subtasks if you want.
- Not all sub-tasks need to be assigned to sub-agent to complete, you can complete some simple tasks yourself.

{TASK_DESCRIPTION}

--- Your Workflow ---
1. You will first be given a task.
2. Then you will start to solve it step by step. Multiple subtasks need to be completed during the solution process. If you cannot solve some subtasks independently, for example, it is difficult or requires the use of external resources, please use "<action>subagent_handle(subtask_name)</action>"  and wait for the response of other agents. After getting a response, continue with the task.
3. Finally, call over() to indicate task completion. After the content in task requirements is completed, call over() immediately without making unnecessary planning.

--- Available Actions ---
1. <action>subagent_handle(subtask_name)</action>
If you want to assign a subtask to other agents for completion, call <action>subagent_handle(subtask_name)</action>
Before you call it, give me the subtask surrounded with <subtask></subtask>.
2. <action>over()</action>
When you think the task is completed, call "<action>over()</action>". After the content in task requirements is completed, call over() immediately without making unnecessary planning.

Now you will be given a task. Start planning and give me an action.
'''

USER_FIRST = '''Task Requirements:
{{task}}
Start your planning until you need to call an action (subagent_handle() or over()). Give me the action between <action> and </action>.'''

USER_PROMPT = """Action Result:\n{{observation}}
Available Actions: {{action_space}}
Continue your planning until you need an action. If the task is completed, call "<action>over()</action>".
"""

USER_OVER_PROMPT = '''Please express the part of the plan that has been confirmed in chronological order in the following formats:
1.go_to_place(origin:str,destination:str,departure_time,arrival_time): go to destination from origin. The origin and destination should be the name of a hotel or a spot instead of a city and they should be in the same city(e.g. go to Wuhan Railway Hotel from Beijing Railway Hotel should use go_to_city()).
2.visit(place:str,begin_time,end_time): visit an attraction(not a city) from begin_time to end_time. The time should be expressed as "%Y-%m-%d %H:%M", e.g. 2023-07-02 16:00. You have to go_to_place() to go somewhere before you can visit it.
3.go_to_city(origin_city:str,destination_city:str,departure_time,arrival_time,ticket_number): go to destination city from origin city, using the ticket with the ticket_number(you can know the ticket number from the database). After use go_to_city(), you will be in the destination_city's Railway Hotel.
4.stay_in(city:str,begin_time,end_time): stay in somewhere from begin_time to end_time. The time should be expressed as "%Y-%m-%d %H:%M". Only when Bob is in some city can he visit it.
You should surround the action between <plan> and </plan> such as <plan>go_to_place(\"Beijing Railway Hotel\",\"The Great Wall\",\
\"2023-07-02 7:00\",\"2023-07-02 8:05\")</plan>, <plan>visit(\"Great Wall\",\
\"2023-07-02 8:05\",\"2023-07-05 17:00\")</plan>,<plan>go_to_city(\"Shanghai\",\"Beijing\",\
\"2023-07-02 16:00\",\"2023-07-02 22:30\",\"D1111\")</plan>, <plan>stay_in(\"Beijing\",\
\"2023-07-02 22:30\",\"2023-07-05 8:00\")</plan>.'''


EXAMPLE_MESSAGES = [{'role': 'system', 'name': 'example_user',
                        'content': '''Task Requirements: Bob is in Shanghai and going to travel in several cities, please make a ticket purchase plan and travel sequence for him.The demands are as follows:
1. visit ['Beijing']. The order doesn't matter and he needs to return to Shanghai finally.
2. He is free to travel from 2023.7.1 to 2023.7.20. The budget for transportation is 1000.0 CNY.
3. Play at least 3 days in Beijing.
4. If you arrive in a city before 12:00 noon, that day can be counted as a day of play. If it's past 12 o'clock, it doesn't count as a day.
5. On the basis of completing the above conditions (especially the budget), spend as little time as possible.
'''},
                       {'role': 'system', 'name': 'example_assistant', 'content':
                           '''THOUGHT:\nBased on the requirements, we can know that Bob need to go to Beijing from Shanghai, stay in Beijing for 3 days and then go to Shanghai from Beijing.
Given the task, the first step is to find available train tickets that fit Bob's schedule and budget. This is a subtask that requires the use of external resources, so I will assign it to another agent.
<subtask>
{
"subtask_name": "find available train tickets",
"goal": "Find train tickets from Shanghai to Beijing and back to Shanghai that fit within the travel dates, budget, and allow for at least 3 full days of play in Beijing. If the arrival is before 12:00 noon, it counts as a day of play.",
"criticism": "Must ensure that the total cost of the round trip tickets does not exceed the budget of 1000.0 CNY and that the timings allow for at least 3 full days in Beijing for visit. So you need to allow time between train rides(arrival in a city and departure from the city). For each ticket, you must give me the ticket number, origin, destination, departure time, arrival time and the price.",
"milestones": ["Identify a suitable train from Shanghai to Beijing.", "Identify a return train from Beijing to Shanghai ensuring at least 3 days in Beijing before departing.", "Ensure the total cost of both tickets is within the budget of 1000.0 CNY."]
}
</subtask>
ACTION:
<action>subagent_handle("find available train tickets")</action>

Once I receive the information about the train tickets, I will proceed with planning the rest of Bob's travel schedule.
'''},

                       {'role': 'system', 'name': 'example_user',
                        'content': '''Action Result:
For Bob's travel from Beijing to Chengdu and back, the updated option is:
- Departure on train **G1371** from Beijing to Chengdu on **2023-07-02 08:57**, arriving at **2023-07-02 17:54**. This costs **747.0 CNY** and takes approximately 8 hours 57 minutes.
- Return on train **K1382** from Chengdu to Beijing on **2023-07-02 19:04**, arriving at **2023-07-03 11:52**. This costs **252.0 CNY** and takes about 16 hours 48 minutes.
The total round trip costs **999.0 CNY** and will take about 25 hours 45 minutes.
For future planning:
With this new itinerary, Bob will be able to spend a full 24 hours in Chengdu.
Bob can now proceed to research places of interest in Chengdu and plan his day accordingly. He can use the 'place' and 'in_city_transport' tables for this purpose.
Bob should also consider the transport options within Chengdu, ensuring he can visit his chosen destinations without spending too much time commuting.
'''},
                       {'role': 'system', 'name': 'example_assistant', 'content':
                           '''THOUGHT:\nNext we can get the final plan. This task is simple so I can do it without other agents. We just need to use go_to_city() and stay_in() here. Based on the information provided, here is the final travel plan for Bob:
<plan>go_to_city("Beijing", "Chengdu", "2023-07-02 08:57", "2023-07-02 17:54", "G1371")</plan>
<plan>stay_in("Chengdu", "2023-07-02 17:54", "2023-07-03 17:54")</plan>
<plan>go_to_city("Chengdu", "Beijing", "2023-07-03 19:04", "2023-07-04 11:52", "K1382")</plan>
ACTION:
The task is completed. <action>over()</over>
'''}]

EXAMPLE_MESSAGES_2 = [{'role': 'system', 'name': 'example_user',
                        'content': '''Task Requirements: Bob is going to play in Wuhan, please make a visit plan for him.The demands are as follows:\n1. He lives in Wuhan Railway Hotel. He needs to visit ['Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', 'Baotong Temple'] and the order can be decided by you.\n2. 2 days(2023-07-06 00:00 ~ 2023-07-08 00:00) for this trip. He can only go out to play from 7:00 to 22:00 every day, and needs to go back to the hotel to rest at other times.\n3. Visit Han Show for 150 minutes, Hubu Alley for 180 minutes, Yellow Crane Tower for 240 minutes, Tan Hua Lin for 240 minutes, Baotong Temple for 300 minutes.\n4. Ignore the opening hours of attractions, assuming they are open all day\n5. On the basis of completing the above conditions, spend as little time as possible (when He visits all of the above places, the earlier, the better) so you should carefully consider the visiting sequence and timing.'''},
                       {'role': 'system', 'name': 'example_assistant', 'content':
                           '''THOUGHT:
To create an efficient travel plan for Bob, our first subtask is to determine the optimal sequence of visits to the five specified locations in Wuhan. This sequence should minimize the overall travel time between these attractions.
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
"subtask_name": "Create a detailed travel and visit plan in Wuhan",
"goal": "Create a detailed travel and visit plan for Bob in Wuhan, including travel to and from 'Tan Hua Lin', 'Baotong Temple', 'Han Show', 'Hubu Alley', and 'Yellow Crane Tower', as well as the duration of each visit.",
"criticism": "The plan may face challenges due to the lack of real-time traffic data and the need to estimate travel times.",
"milestones": [
"Retrieve travel times between places from the database.",
"Schedule each activity (travel and visit) within the allowed time frame (7:00 to 22:00 each day).",
"Ensure the total visit time at each attraction meets the specified duration.",
"Compile the final itinerary in a coherent and chronological order."
],
"result_format": "A schedule consisting with multiple <plan>go_to_place(origin,destination,departure_time,arrival_time)</plan> and <plan>visit(place,begin_time,end_time)</plan>."
}</subtask>
Then we can get the final plan and call over().
Now we first let another agent solve subtask1. 
ACTION:
<action>subagent_handle("Optimal Visit Sequence In Wuhan")</action>
We will need to wait for the results from the other agents before we can proceed to the next step of the task.
'''},

                       {'role': 'system', 'name': 'example_user',
                        'content': '''Action:
<action>subagent_handle("Optimal Visit Sequence")</action>
Result:
The optimal visit sequence is ['Tan Hua Lin', 'Baotong Temple', 'Han Show', 'Hubu Alley', 'Yellow Crane Tower']. ......
'''}]

EXAMPLE_MESSAGES_3 = [{'role': 'system', 'name': 'example_user',
                        'content': '''Task Requirements: Bob is going to visit some spots across cities, please make a visit plan for him, including inter-city transportation, intra-city transportation, and visit time for each spot.The demands are as follows:\n1. He now lives in Wuhan Railway Hotel in Wuhan. In Guangzhou, he needs to visit Canton Tower for 150 minutes, Baiyun Mountain for 210 minutes.In Hangzhou, he needs to visit China National Tea Museum for 120 minutes, Quaint Water Towns for 150 minutes, Lingyin Temple for 240 minutes, West Lake for 180 minutes. And the order can be decided by you.\n2. 5 days (2023-07-9 07:00 ~ 2023-07-14 00:00) for this trip.\n3. Ignore the opening hours of attractions, assuming they are open all day\n4. On the basis of completing the above conditions (especially the time limit), spend as little money as possible.
'''},
                       {'role': 'system', 'name': 'example_assistant', 'content':
                           '''
THOUGHT:\nBased on the requirements, Bob need to visit ["Guanzhou","Hangzhou"] and now he is in Wuhan. A simple way is to first find a random order of the cities. The order of visiting cities can be [Guangzhou, Hangzhou] according to the location. So he needs to: 1. go to Guangzhou from Wuhan. 2. visit apots in Wuhan. 3.go to Hangzhou from Wuhan. 4.visit Hangzhou. Then the task is completed.
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
"subtask_name": "Create a detailed travel and visit plan in Guangzhou",
"goal": "Create a detailed travel and visit plan for Bob in Guangzhou, including travel to and from 'Canton Tower' and 'Baiyun Mountain', as well as the duration of each visit.",
"criticism": "Time management is crucial to ensure Bob spends the required time at each attraction. Also, consider the time spent in traffic from one place to another.",
"milestones": ["Decide visit order", "Calculate travel time between spots and the time for visiting", "Arrange transportation and visit schedule starting from Guangzhou Railway Hotel,including go_to_place() and visit(). The begin time is determined by the results of the previous subtasks."],
"result_format": "A schedule consisting with multiple <plan>go_to_place(origin,destination,departure_time,arrival_time)</plan> and <plan>visit(place,begin_time,end_time)</plan>."
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
"subtask_name": "Create a detailed travel and visit plan in Hangzhou",
"goal": "Create a detailed travel and visit plan for Bob in Hangzhou, including travel to and from 'China National Tea Museum', 'Quaint Water Towns', 'Lingyin Temple', and 'West Lake', as well as the duration of each visit.",
"criticism": "Time management is crucial to ensure Bob spends the required time at each attraction. Also, consider the time spent in traffic from one place to another.",
"milestones": ["Decide visit order", "Calculate visit and travel time between spots", "Arrange transportation and visit schedule starting from Hangzhou Railway Hotel. The begin time is determined by the results of the previous subtasks."],
"result_format": "A schedule consisting with multiple <plan>go_to_place(origin,destination,departure_time,arrival_time)</plan> and <plan>visit(place,begin_time,end_time)</plan>."
}
</subtask>
Then we can get the final plan and call over().
Now we first let another agent solve subtask 1 to get the departure_time, arrival_time and ticket_number for <plan>go_to_city()</plan>.
ACTION:\n<action>subagent_handle("Find available train tickets from Wuhan to Guangzhou")</action>
We need to wait for the results from the other agents before we can take the next action.
'''},
                       {'role': 'system', 'name': 'example_user',
                        'content': '''Action:
<action>subagent_handle("Find available train tickets from Wuhan to Guangzhou")</action>
Result: Bob can take the train "G2034". The information is as follows:
ticket number: "G2034", departure time: "2023-07-09 13:00", arrival time: "2023-07-09 20:00".
He can start his visit in Guangzhou next day(2023-07-10 07:00).'''},

                       {'role': 'system', 'name': 'example_assistant', 'content':
                           '''Thought: good! Then we should arrange his visits in Guangzhou, including <plan>go_to_place(...)</plan> and <plan>visit(...)</plan>. According to the result of subtask 1, we can know that the begin_time in subtask 2 is 2023-07-10 07:00 and we need to make some adjustments to subtask2, as follows:
Subtask 2: Arranging Intra-city Transportation and Visits in Guangzhou
<subtask>
{
"subtask_name": "Create a detailed travel and visit plan in Guangzhou",
"goal": "Create a detailed travel and visit plan for Bob in Guangzhou, including travel to and from 'Canton Tower' and 'Baiyun Mountain', as well as the duration of each visit.",
"criticism": "Time management is crucial to ensure Bob spends the required time at each attraction and has enough time to transfer to the next city. Also, consider traffic conditions and travel time between spots.",
"milestones": ["Determine the tour route", "Arrange transportation and visit schedule starting from Guangzhou Railway Hotel at 2023-07-10 07:00."],
"result_format": "A schedule consisting with multiple <plan>go_to_place(origin,destination,departure_time,arrival_time)</plan> and <plan>visit(place,begin_time,end_time)</plan>.    1.go_to_place(origin:str,destination:str,departure_time,arrival_time): go to destination from origin. depart at departure_time and arrive at arrival_time.    2.visit(place:str,begin_time,end_time): visit somewhere from begin_time to end_time. You have to go somewhere before you can visit it."}
</subtask>
ACTION:<action>subagent_handle("Create a detailed travel and visit plan in Guangzhou")</action>
'''}
                       ]
