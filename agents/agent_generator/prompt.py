ORIGINAL_DOCUMENT = """<action>execute_sql(statement:string)</action>
You can use the action ’execute_sql’ to get some information from the database.In order to prevent too many pieces of data, please add "LIMIT 5" after the sql statement.

Tables in the database are as follows.
Table railway:
CREATE TABLE railway(
            number TEXT, /*Ticket Number*/ 
            origin TEXT,
            destination TEXT,
            departure_time DATETIME,
            arrival_time DATETIME,
            duration INTEGER, /*Duration of the train journey in minutes*/
            price REAL
        )
From table railway, you can filter the items according to the origin, destination, and departure date, and then plan according to the obtained information. Don’t use duration as a filtering condition.
If you buy a ticket, please point out the number of it. 

Table place:
CREATE TABLE place(
    name TEXT,
    city TEXT,
    type TEXT,
    opening_hours_begin INTEGER,
    opening_hours_end INTEGER
)
From table place, you can filter the items according to the city to know some information of places in this city.

Table in_city_transport:
CREATE TABLE in_city_transport(
    origin TEXT,
    destination TEXT,
    duration INTEGER, /*indicates how many minutes are spent in traffic*/
    city TEXT
)

From table in_city_transport, you can know how long you may spend from origin to destination.
Before visiting a spot, you must spend time going to this spot from the hotel or another spot.

Be careful to set conditions, otherwise too many items will be retrieved from the database.
Usage examples:
<action>execute_sql('''
SELECT * FROM place
WHERE city = 'Beijing';''')</action>
<action>execute_sql('''
SELECT origin, destination, duration FROM in_city_transport
    WHERE city = 'Hangzhou' AND 
    (origin IN ('West Lake', 'Lingyin Temple', 'Hefang Street', 'Quaint Water Towns') AND 
    destination IN ('West Lake', 'Lingyin Temple', 'Hefang Street', 'Quaint Water Towns'));''')</action> 
<action>execute_sql('''
SELECT * FROM railway
WHERE origin = 'Beijing'
  AND destination = 'Shanghai'
  AND DATE(departure_time) >= '2023-07-25'
  LIMIT 5;''')</action>. 


<action>execute_python(code:string)</action>
You can use the action ‘execute_python()’ to assist your planning. You must use print() in the python code to get what you want to know. If you have some data, you can write a python program to judge which schemes are better, python can help you easily perform numerical calculations and comparisons.
You can use dynamic programming, greedy algorithm or direct traversal to get the better plan.
The code must be complete and directly executable. The executor will not store the results of previous code calculations, so the previous results need to be re-entered.
The python code should be surrounded by \"\"\" and \"\"\".
e.g.
<action>execute_python(\"\"\"
price=[540, 300, 210]
print(f 'The total cost is {{sum(price)}}')
\"\"\")</action>
"""

SYSTEM_PROMPT = f"""
You are a prompt generator, who is capable of generating prompts for an autonomous agent.
You will be told a subtask that the agent needs to complete. The subtask is part of the total task.
You need to optimize the following documents based on the tasks (subtask) that the agent needs to complete.
This agent use actions completely according to the following document. Please provide the agent with a prompt for the action instructions. You don't need to complete the task, but optimize the document. The optimized document will be given to the agent so that it can use the action correctly.
The original document is as follows：
<original Action Document>{ORIGINAL_DOCUMENT}</original Action Document>

*** Important Notice ***
- Surround the new document with <action document></action document>.
- You don't need to complete the task, but optimize the document.  The optimized document will be given to the agent so that it can use the action correctly.
- Optimize the document by combining the total tasks and subtasks. For example, the agent may not need all the content of the document. Only give the actions required to complete the subtask.
- Try not to delete details in the document so that the agent cannot use the action correctly. For example, sometimes some tables in the database can be deleted.
"""

EXAMPLE_MESSAGES = [{'role': 'system', 'name': 'example_user',
                     'content': '''<agent task>
The subtask the agent need to complete is:
{'subtask_name': 'find_available_train_tickets', 'goal': 'Find train tickets from Shanghai to Beijing and back to Shanghai that fit within the travel dates, budget, and allow for at least 3 full days of play in Beijing. If the arrival is before 12:00 noon, it counts as a day of play.', 'criticism': 'Must ensure that the total cost of the round trip tickets does not exceed the budget of 1000.0 CNY and that the timings allow for at least 3 full days in Beijing for visit. So you need to allow time between train rides(arrival in a city and departure from the city). For each ticket, you must give me the ticket number, origin, destination, departure time, arrival time and the price.', 'milestones': ['Identify a suitable train from Shanghai to Beijing.', 'Identify a return train from Beijing to Shanghai ensuring at least 3 days in Beijing before departing.', 'Ensure the total cost of both tickets is within the budget of 1000.0 CNY.']}
The total task is: 
Bob is in Shanghai and going to travel in several cities, please make a ticket purchase plan and travel sequence for him.The demands are as follows:
1. visit ['Beijing']. The order doesn't matter and he needs to return to Shanghai finally.
2. He is free to travel from 2023.7.1 to 2023.7.20. The budget for transportation is 1000.0 CNY.
3. Play at least 3 days in Beijing.
4. If you arrive in a city before 12:00 noon, that day can be counted as a day of play. If it's past 12 o'clock, it doesn't count as a day.
5. On the basis of completing the above conditions (especially the budget), spend as little time as possible.
The part that has been completed is:
None
</agent task>
Now you need to give me the optimized document based on the tasks (subtask) that the agent needs to complete. Surround the new document with <action document></action document>.
'''},
                    {'role': 'system', 'name': 'example_assistant', 'content':
                        """THOUGHT: Given that the subtask that the agent need to complete is:
{
"sub-task name": "Research Transportation Options",
"goal": "Find the most cost-effective and time-saving transportation options from Beijing to Chengdu and back to Beijing within the budget of 1800.0 CNY.",
"criticism": "If the transportation options exceed the budget, we will need to find alternatives or adjust the itinerary. Additionally, scheduling might pose a challenge if there are limited options.",
"milestones": [
"Determine available transport modes from Beijing to Chengdu (train, bus, flight).",
"Find the costs associated with each transportation mode.",
"Optimize the selection based on cost and travel time.",
"Ensure that the total round trip transportation cost is within 1800.0 CNY."
]} The agent needs to use:
1.<action>execute_python(code:string)</action> to calculate the costs for different transport modes and optimize the selection based on cost and travel time within the given budget.
2.<action>execute_sql(statement:string)</action> to get the information of train tickets. Only Table railway is useful for this subtask.
So the optimized document is as follows:
DOCUMENT:
<action document>
<action>execute_sql(statement:string)</action>
You can use the action ’execute_sql’ to get some information from the database.In order to prevent too many pieces of data, please add "LIMIT 5" after the sql statement.

Tables in the database are as follows.
Table railway:
CREATE TABLE railway(
            number TEXT, /*Ticket Number*/ 
            origin TEXT,
            destination TEXT,
            departure_time DATETIME,
            arrival_time DATETIME,
            duration INTEGER, /*Duration of the train journey in minutes*/
            price REAL
        )
From table railway, you can filter the items according to the origin, destination, and departure date, and then plan according to the obtained information. Don’t use duration as a filtering condition.
If you buy a ticket, please point out the number of it. 

Be careful to set conditions, otherwise too many items will be retrieved from the database.
Usage examples:
<action>execute_sql('''
SELECT * FROM railway
WHERE origin = 'Beijing'
  AND destination = 'Shanghai'
  AND DATE(departure_time) >= '2023-07-25'
  LIMIT 5;''')</action>. 

<action>execute_python(code:string)</action>
You can use the action ‘execute_python()’ to assist your planning. You must use print() in the python code to get what you want to know. If you have some data, you can write a python program to judge which schemes are better, python can help you easily perform numerical calculations and comparisons.
You can use dynamic programming, greedy algorithm or direct traversal to get the better plan.
The code must be complete and directly executable. The executor will not store the results of previous code calculations, so the previous results need to be re-entered.
If you want to use execute_sql in execute_python, add 'from utils.travel import execute_sql' in python code.
The python code should be surrounded by \"\"\" and \"\"\".
e.g.
<action>execute_python(\"\"\"
price=[540, 300, 210]
print(f 'The total cost is {{sum(price)}}')
\"\"\")</action>
</action document>.
"""},
                    {'role': 'system', 'name': 'example_user',
                     "content":"""<agent task>
The subtask the agent need to complete is:
{'subtask_name': 'Optimal Visit Sequence In Wuhan', 
'goal': "Find the most efficient sequence for visiting 'Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', and 'Baotong Temple' in Wuhan. This involves determining the order that minimizes travel time between these attractions.", 
'criticism': 'The challenge is in accurately estimating travel times between different locations without real-time data. The chosen sequence might not be the absolute best due to unforeseen circumstances like traffic conditions.', 
'milestones': ["Determine the locations of 'Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', and 'Baotong Temple'.", 'Estimate the travel time between each pair of attractions.', 'Use an algorithm or heuristic to find the sequence of visits that minimizes the total travel time.', 'Confirm the final sequence for the visits.'], 
'result_format': 'a list of spots to visit'}
The total task is: 
Bob is going to play in Wuhan, please make a visit plan for him.The demands are as follows:
1. He lives in Wuhan Railway Hotel. He needs to visit ['Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', 'Baotong Temple'] and the order can be decided by you.
2. 2 days(2023-07-06 00:00 ~ 2023-07-08 00:00) for this trip. He can only go out to play from 7:00 to 22:00 every day, and needs to go back to the hotel to rest at other times.
3. Visit Han Show for 150 minutes, Hubu Alley for 180 minutes, Yellow Crane Tower for 240 minutes, Tan Hua Lin for 240 minutes, Baotong Temple for 300 minutes.
4. Ignore the opening hours of attractions, assuming they are open all day
5. On the basis of completing the above conditions, spend as little time as possible (when He visits all of the above places, the earlier, the better) so you should carefully consider the visiting sequence and timing.
The part that has been completed is:
None
</agent task>
Now you need to give me the optimized document based on the tasks (subtask) that the agent needs to complete. Surround the new document with <action document></action document>.
"""},
{'role': 'system', 'name': 'example_assistant', 'content':
                        """THOUGHT: Given that the subtask that the agent need to complete is:
{'subtask_name': 'Optimal Visit Sequence In Wuhan', 
'goal': "Find the most efficient sequence for visiting 'Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', and 'Baotong Temple' in Wuhan. This involves determining the order that minimizes travel time between these attractions.", 
'criticism': 'The challenge is in accurately estimating travel times between different locations without real-time data. The chosen sequence might not be the absolute best due to unforeseen circumstances like traffic conditions.', 
'milestones': ["Determine the locations of 'Han Show', 'Hubu Alley', 'Yellow Crane Tower', 'Tan Hua Lin', and 'Baotong Temple'.", 'Estimate the travel time between each pair of attractions.', 'Use an algorithm or heuristic to find the sequence of visits that minimizes the total travel time.', 'Confirm the final sequence for the visits.'], 
'result_format': 'a list of spots to visit'} The agent needs to use:
1.<action>execute_python(code:string)</action> to calculate the time spent for different visit sequences and perform other timing calculations.
2.<action>execute_sql(statement:string)</action> to get the travel time between spots and get some information about spots. Table place and in_city_transport are useful for this subtask.
So the optimized document is as follows:
DOCUMENT:
<action document>
<action>execute_sql(statement:string)</action>
You can use the action ’execute_sql’ to get some information from the database.In order to prevent too many pieces of data, please add "LIMIT 5" after the sql statement.

Tables in the database are as follows.

Table place:
CREATE TABLE place(
    name TEXT,
    city TEXT,
    type TEXT,
    opening_hours_begin INTEGER,
    opening_hours_end INTEGER
)
From table place, you can filter the items according to the city to know some information of places in this city.

Table in_city_transport:
CREATE TABLE in_city_transport(
    origin TEXT,
    destination TEXT,
    duration INTEGER, /*indicates how many minutes are spent in traffic*/
    city TEXT
)

From table in_city_transport, you can know how long you may spend from origin to destination.
Before visiting a spot, you must spend time going to this spot from the hotel or another spot.

Be careful to set conditions, otherwise too many items will be retrieved from the database.
Usage examples:
<action>execute_sql('''
SELECT * FROM place
WHERE city = 'Beijing';''')</action>
<action>execute_sql('''
SELECT origin, destination, duration FROM in_city_transport
    WHERE city = 'Hangzhou' AND 
    (origin IN ('West Lake', 'Lingyin Temple', 'Hefang Street', 'Quaint Water Towns') AND 
    destination IN ('West Lake', 'Lingyin Temple', 'Hefang Street', 'Quaint Water Towns'));''')</action> 
    

<action>execute_python(code:string)</action>
You can use the action ‘execute_python()’ to assist your planning. You must use print() in the python code to get what you want to know. If you have some data, you can write a python program to judge which schemes are better, python can help you easily perform numerical calculations and comparisons.
You can use dynamic programming, greedy algorithm or direct traversal to get the better plan.
The code must be complete and directly executable. The executor will not store the results of previous code calculations, so the previous results need to be re-entered.
The python code should be surrounded by \"\"\" and \"\"\".
e.g.
<action>execute_python(\"\"\"
price=[540, 300, 210]
print(f 'The total cost is {{sum(price)}}')
\"\"\")</action>
</action document>.
"""}
]

TOTAL_TASK = """Bob is in Beijing and going to travel in several cities, please make a ticket purchase plan and travel sequence for him.The demands are as follows:
1. visit ['Chengdu']. The order doesn't matter and he needs to return to Beijing finally.
2. He is free to travel from 2023.7.1 to 2023.7.20. The budget for transportation is 1800.0 CNY.
3. Play at least 1 day in Chengdu.
4. Stay in any city for a minimum of 24 hours to count as one day.
5. On the basis of completing the above conditions (especially the budget), spend as little time as possible."""

CURRENT_TASK = """{
"sub-task name": "Research Transportation Options",
"goal": "Find the most cost-effective and time-saving transportation options from Beijing to Chengdu and back to Beijing within the budget of 1800.0 CNY.",
"criticism": "If the transportation options exceed the budget, we will need to find alternatives or adjust the itinerary. Additionally, scheduling might pose a challenge if there are limited options.",
"milestones": [
"Determine available transport modes from Beijing to Chengdu (train, bus, flight).",
"Find the costs associated with each transportation mode.",
"Optimize the selection based on cost and travel time.",
"Ensure that the total round trip transportation cost is within 1800.0 CNY."
]"""

COMPLETED_TASK = 'None'

USER_FIRST_PROMPT = """<agent task>
The subtask the agent need to complete is:\n{{current_task}}
The total task is: \n{{total_task}}
The part that has been completed is:\n{{completed_task}}
</agent task>
Now you need to give me the optimized document based on the tasks (subtask) that the agent needs to complete. Surround the new document with <action document></action document>."""
