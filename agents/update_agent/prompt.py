SYSTEM_PROMPT = f"""You are a helpful assistant."""

USER_FIRST_PROMPT = """
There two tasks with their respective solutions: 
Task 1: {{task1}}
Solution 1: {{solution1}}
Task 2: {{task2}}
Solution 2: {{solution2}}"""+"""Your task is to analyze both solutions and determine the following:
Assess whether the solution for Task 2 (Solution 2) can be applied to or is relevant for solving Task 1. Please provide a detailed analysis of the compatibility and effectiveness of Solution 2 in the context of Task 1.
If you find that Solution 2 can indeed assist in solving Task 1, I need you to update Solution 1 accordingly. In your revised Solution 1, include any necessary modifications or enhancements that incorporate elements from Solution 2. Please ensure that the updated solution is practical and addresses any potential issues or considerations that may arise from the integration of these two solutions. If there is no great reference value, try not to update solution1. If you update, please make as small changes as possible to keep the final solution concise and clear.
If you think Solution 1 should be updated, say \"<action>update(solution_content)</action>\". solution_content is a string surrounded by \"\". It only needs to contain the content of the solution and be as simple and clear as possible. Do not mention the words like "task1", "task2", "update", and "solution1" in solution_content, because the solution cannot reflect that this solution refers to other solutions.
Otherwise say \"<action>keep()</action>\". Remember to surround the update() or keep() between <action> and </action>\n"""

