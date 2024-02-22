import json
import numpy as np
from sentence_transformers import SentenceTransformer, util
import os
import random

from sentence_transformers import SentenceTransformer, util


def get_similarity(text1, text2, model_name='all-mpnet-base-v2'):
    """
    Calculate the cosine similarity between two text strings.

    Args:
    text1 (str): The first text string.
    text2 (str): The second text string.
    model_name (str): The name of the SentenceTransformer model to use.

    Returns:
    float: The cosine similarity between text1 and text2.
    """
    # Load the SentenceTransformer model
    model = SentenceTransformer(model_name)

    # Encode the texts into embeddings
    embedding1 = model.encode(text1, convert_to_tensor=True)
    embedding2 = model.encode(text2, convert_to_tensor=True)

    # Calculate cosine similarity
    similarity = util.pytorch_cos_sim(embedding1, embedding2)

    return similarity.item()


def encode_tasks(model, tasks, embeddings_file, rewrite=False):
    if os.path.exists(embeddings_file) and not rewrite:
        embeddings = np.load(embeddings_file)
    else:
        embeddings = model.encode(tasks, convert_to_tensor=True)
        np.save(embeddings_file, embeddings)
    return embeddings


def find_similar_tasks(embedding, embeddings, num_solutions=1):
    similarities = util.pytorch_cos_sim(embedding, embeddings)[0]
    most_similar_indices = np.argsort(-similarities)[:num_solutions]
    return most_similar_indices


def get_prompt(task_name, task_detail, solution_num=1, example_file='./data/travel/skill.json', rewrite=True,
               reverse=True, theta=None, use_detail=True):
    example_file_name = example_file[:example_file.rfind('.json')]
    name_embeddings_file = f'{example_file_name}_name_embedding.npy'
    detail_embeddings_file = f'{example_file_name}_detail_embedding.npy'
    model_name = 'all-mpnet-base-v2'

    with open(example_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    if solution_num >= len(data):
        results = []
        for d in data:
            result = f"Example Task Name:\n{d['task_name']}\nExample Task Detail:\n{d['task_detail']}\nExample Solution:\n{d['solution']}\n"
            results.append(result)
        return '\n'.join(results[::])

    task_names = [item['task_name'] for item in data]
    task_details = [item['task_detail'] for item in data]
    model = SentenceTransformer(model_name)
    name_embeddings = encode_tasks(model, task_names, name_embeddings_file, rewrite)
    detail_embeddings = encode_tasks(model, task_details, detail_embeddings_file, rewrite)

    # Initial filtering based on task name
    current_task_name_embedding = model.encode(task_name, convert_to_tensor=True)

    if use_detail:
        similar_name_indices = find_similar_tasks(current_task_name_embedding, name_embeddings, solution_num * 2)
    else:
        similar_name_indices = find_similar_tasks(current_task_name_embedding, name_embeddings, solution_num)
    # Further filtering based on task detail
    current_task_detail_embedding = model.encode(task_detail, convert_to_tensor=True)
    filtered_task_details = [task_details[i] for i in similar_name_indices]
    filtered_detail_embeddings = detail_embeddings[np.array(similar_name_indices)]
    similar_detail_indices = find_similar_tasks(current_task_detail_embedding, filtered_detail_embeddings, solution_num)

    results = []
    for idx in similar_detail_indices:
        index = similar_name_indices[idx.item()]
        similar_task = data[index]
        if theta is not None:
            if len(results)>0 and get_similarity(similar_task['task_name'], task_name) < theta:
                continue
        result = f"Example Task Name:\n{similar_task['task_name']}\nExample Task Detail:\n{similar_task['task_detail']}\nExample Solution:\n{similar_task['solution']}\n"
        results.append(result)

    if reverse:
        return '\n'.join(results[::-1])
    return '\n'.join(results[::])
