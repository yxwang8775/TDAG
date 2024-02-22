SYSTEM_PROMPT = """You are a checker, and you need to check an agent's completion of subtasks. \
I will tell you the overall tasks, completed tasks, and the agent's completion of tasks.\
Please evaluate the agent's behavior. If you think it completed the task correctly, \
please say <action>success()</action>, otherwise please say <action>fail(reason)</action>, \
reason is a string surrounded by "", explanation The reason why the agent did not complete the task correctly.

The overall task is: \n{{total_task}}\n
The part that has been completed so far is \n{{completed_task}}\n
And the sub-task that this agent need to complete is:\n{{current_task}}\n

The result given by the agent is:\n{{result}}\n
Its completion process is:\n"{{process}}"\n

Just check whether the final result meets the requirements in the subtask.
"""

result = """For Bob's travel from Beijing to Chengdu and back, the most time-efficient and cost-effective option is:
- Departure on train G1371 from Beijing to Chengdu on 2023-07-02 at 08:57, arriving at 17:54. This costs 747.0 CNY and takes approximately 8 hours 57 minutes.
- Return on train G1698 from Chengdu to Beijing on 2023-07-03 at 06:09, arriving at 13:22. This costs 840.0 CNY and takes about 7 hours 13 minutes.
The total round trip costs 1587.0 CNY and will take about 16 hours 10 minutes.
For future planning:

Since Bob is only spending one day in Chengdu, he might want to optimize his sightseeing itinerary to make the most of his visit.
Bob can now proceed to research places of interest in Chengdu and plan his day accordingly. He can use the 'place' and 'in_city_transport' tables for this purpose.
Bob should also consider the transport options within Chengdu, making sure he can visit his chosen destinations without spending too much time commuting.
"""

process = """1. First, I reviewed the sub-task which was to find the most cost-effective and time-saving transportation options from Beijing to Chengdu and back to Beijing within the budget of 1800.0 CNY.
2. I used the `execute_sql` action to retrieve available train options from Beijing to Chengdu within the specified date range.
3. After obtaining the data, I analyzed the options to find the most time-efficient while staying within budget.
4. Similarly, I fetched train options from Chengdu to Beijing to finalize the round trip.
5. After analyzing both departure and return options, the best choices were suggested based on minimal travel time and budget considerations.
"""


TOTAL_TASK = """Bob is in Beijing and going to travel in several cities, please make a ticket purchase plan and travel sequence for him.The demands are as follows:
1. visit ['Chengdu']. The order doesn't matter and he needs to return to Beijing finally.
2. He is free to travel from 2023.7.1 to 2023.7.20. The budget for transportation is 1800.0 CNY.
3. Play at least 1 day in Chengdu.
4. Stay in any city for a minimum of 24 hours to count as one day.
5. On the basis of completing the above conditions (especially the budget), spend as little time as possible."""

current_task = """{
"sub-task name": "Research Transportation Options",
"goal": "Find the most cost-effective and time-saving transportation options from Beijing to Chengdu and back to Beijing within the budget of 1800.0 CNY.",
"criticism": "If the transportation options exceed the budget, we will need to find alternatives or adjust the itinerary. Additionally, scheduling might pose a challenge if there are limited options.",
"milestones": [
"Determine available transport modes from Beijing to Chengdu (train, bus, flight).",
"Find the costs associated with each transportation mode.",
"Optimize the selection based on cost and travel time.",
"Ensure that the total round trip transportation cost is within 1800.0 CNY."
]"""

completed_task = 'None'
