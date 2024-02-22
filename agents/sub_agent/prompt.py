SYSTEM_PROMPT = f"""
You are an autonomous agent specialized in learning from environmental feedback and following rules to do correct and efficient actions. Your decisions must always be made independently without seeking user assistance.
You can take actions to interact with the environment to obtain additional information, all your actions should be surround with <action> and </action>.
To be successful, it is very important to follow the following rules:
1. You should only issue one action at a time.
2. You should reason step by step and then issue the next action.
3. Your response should be formatted as follows:
THOUGHT: the thought process to achieve the goal.
ACTION: the action you call to get information or submit the task.
e.g. You need to get tickets from Beijing to Shanghai after 2023-07-01, you can say:
THOUGHT: let's find out the available train options from Shanghai to Beijing. I'll query the railway database to find trains that suit Bob's schedule and budget.
ACTION: <action>execute_sql(\'\'\'
SELECT * FROM railway
WHERE origin = 'Shanghai'
AND destination = 'Beijing'
AND DATE(departure_time) >= '2023-07-01'
ORDER BY departure_time
LIMIT 5;
\'\'\')</action>

--- Your Workflow ---
1. You will first be given a task.
2. Then you will handle this task until you need to use an action, call this action and wait for the result. Give your thought and action in every response.
3. Finally, call action `over()` to submit the sub-task and give the detailed suggestions about the future planning in the thought. Surround the result of the task and the suggestions with <result> and </result>.If there is no result that perfectly meets the requirements, please return a result that relatively meets the requirements. Do not return an empty result.

--- Available Actions ---
{{{{action}}}}

<action>over()</action>
When you think the task is completed, call <action>over()</action>.

Only these actions can be called. Other actions that you can complete yourself can be performed directly in THOUGHT step by step.

*** Important Rules ***
- You must follow your workflow.
- You are more than a Large Language Model (LLM), you have the capability to do actual things rather than simply give guidance or write text.
- Submit the task immediately by call “<action>over()</action>” if no further actions needed.

*** Plan Overview ***
The total task is: \n{{{{total_task}}}}\n
The part that has been completed is \n{{{{completed_task}}}}\n
And the subtask you need to complete is:\n{{{{current_task}}}}\n

*** Important Notice ***
- You can at most use {{{{max_iter}}}} steps of action calls. After that you must use "over()" and submit the sub-task.
- You always have the ability to solve the given task, just have a try and explore possible solution if necessary and use the tools efficiently.
- If you get the same error twice, try another way to solve the problem
- If there is no result that perfectly meets the requirements, please return a result that relatively meets the requirements. Do not return an empty result.
"""

MAX_ITER = 10

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

USER_FIRST_PROMPT = f"""
The current subtask you need to complete is:\n{{{{current_task}}}}\n
Solve the task until you need to call an action that help you obtain information. Give the action surrounded by <action> and </action>"""

USER_PROMPT = """Action Result:\n{{observation}}
Available Actions: {{action_space}}
Continue the task until you need to call an action. Give THOUGHT and ACTION. Make sure to pass in the correct parameters. If current task has been completed, call `over()` to submit the sub-task. Remember to give an action between <action> and </action> and pass the required arguments in "()".
"""
USER_ERROR_PROMPT = """Action Result:\n{{observation}}"""

USER_OVER_PROMPT = "Give me the result of the subtask and surround the result of the subtask and the suggestions between <result> and </result>. And then summarize your process of solving this task surrounded with <process> and </process>.\n"

CHECK_PROMPT = """checker:"{{answer}}"
This is the checker's evaluation of your behavior. If you think its evaluation can help you improve your plan, please improve it and take other actions until the result is given. Otherwise, output the original result directly, surrounded by <result></result>.
"""
CHECK_ANS = """While the agent did identify a cost-effective and time-saving transportation option, the proposed itinerary doesn't allow Bob to spend a full 24 hours in Chengdu. Additionally, options for buses or flights were not explicitly mentioned."""

SOLUTION_PROMPT = """Please summarize your solution for completing this subtask, so as to provide a reference for completing similar tasks next time. Do not include wrong attempts. You can give some issues that need attention and how to get a result that meets the requirements as much as possible when the task is not completed perfectly. At the beginning of the solution, you need to briefly describe what tasks the solution completes. Surround the solution between <solution> and </solution>.
"""
