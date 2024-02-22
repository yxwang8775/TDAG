from agents.react_agent.agent import ReactAgent

task="""Task Requirements: Bob is going to visit some spots across cities, please make a visit plan for him, including inter-city transportation, intra-city transportation, and visit time for each spot.The demands are as follows:\n1. He now lives in Wuhan Railway Hotel in Wuhan. In Guangzhou, he needs to visit Canton Tower for 150 minutes, Baiyun Mountain for 210 minutes.In Hangzhou, he needs to visit China National Tea Museum for 120 minutes, Quaint Water Towns for 150 minutes, Lingyin Temple for 240 minutes, West Lake for 180 minutes. And the order can be decided by you.\n2. 5 days (2023-07-9 07:00 ~ 2023-07-14 00:00) for this trip.\n3. Ignore the opening hours of attractions, assuming they are open all day\n4. On the basis of completing the above conditions (especially the time limit), spend as little money as possible."""

agent = ReactAgent(task=task, record_path='.', example_message=[])
#
# print(agent.system_prompt)

# observation='''{'query': "\nSELECT * FROM railway\nWHERE origin = 'Shanghai'\n  AND destination = 'Beijing'\n  AND DATE(departure_time) >= '2023-07-01'\n  LIMIT 5;", 'result': [['D1003', 'Shanghai', 'Beijing', '2023-07-01 22:54', '2023-07-02 09:29', 635, 300.0], ['G1008', 'Shanghai', 'Beijing', '2023-07-01 06:29', '2023-07-01 13:19', 410, 580.0], ['G1013', 'Shanghai', 'Beijing', '2023-07-01 10:32', '2023-07-01 17:11', 399, 580.0], ['G1016', 'Shanghai', 'Beijing', '2023-07-01 17:05', '2023-07-01 20:27', 202, 680.0], ['D1325', 'Shanghai', 'Beijing', '2023-07-02 18:41', '2023-07-03 08:40', 839, 300.0]], 'error': None}'''
# agent.add_user_prompt(observation=observation)
# print(agent.messages[-1])
# print(agent.system_prompt)
from utils.travel import execute_sql,execute_python
result=execute_sql('''
SELECT * FROM railway
WHERE origin = 'Wuhan'
AND destination = 'Guangzhou'
AND DATE(departure_time) >= '2023-07-09'
LIMIT 5;''')
agent.add_user_prompt(observation=result)
print(agent.messages[-1])
#
# print(execute_python('print(\'Helloworld\')'))
#
# result=execute_python("""
# from itertools import permutations
#
# # Travel durations from Wuhan Railway Hotel to each destination in minutes
# travel_times = {
# 'Yellow Crane Tower': 72,
# 'Han Show': 42,
# 'Baotong Temple': 46,
# 'Tan Hua Lin': 20,
# 'Hubu Alley': 54
# }
#
# # Duration Bob wants to spend at each place in minutes
# visit_durations = {
# 'Han Show': 150,
# 'Hubu Alley': 180,
# 'Yellow Crane Tower': 240,
# 'Tan Hua Lin': 240,
# 'Baotong Temple': 300
# }
#
# # Generate all possible orders of visiting the places
# possible_orders = permutations(travel_times.keys())
#
# # Function to calculate total time for a given order
# def calculate_total_time(order):
# total_time = 0
# current_location = 'Wuhan Railway Hotel'
# for place in order:
# # Add travel time to the place
# total_time += travel_times[place]
# # Add time spent at the place
# total_time += visit_durations[place]
# current_location = place
# return total_time
#
# #Find the order with the minimum total time
# min_time = float('inf')
# best_order = None
# for order in possible_orders:
# total_time = calculate_total_time(order)
# if total_time < min_time:
# min_time = total_time
# best_order = order
#
# print(f'The best order to visit is: {best_order} with a total time of {min_time} minutes.')
# """)
#
# print(result)