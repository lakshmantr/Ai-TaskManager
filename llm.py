import requests
from stt import transcript
import json
from tts import audio_generator
import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}
prompt = """
You are a task manager assistant.
Based on the user's command, extract the intent and relevant details.
Respond only in JSON format with the following rules:
1. If the user is **adding a task**, include:
   - "intent": "add_task"
   - "task": the name/title of the task
   - "time": the scheduled time (if provided)
   - "description": task description (if provided)
2. If the user is **updating a task**, include:
   - "intent": "update_task"
   - "task": the task being updated
   - "status": the new status of the task (e.g., "completed", "pending")
   - "description": any updated description (if provided)
   - "time": any updated time  (if provided,if the user says update the task so and so from this time to another time then provide just the time the task has to be updated to )
3. If the user is **deleting a task**, include:
   - "intent": "delete_task"
   - "task": the task being deleted
   - "time": the scheduled time (if known)
4. If the user is **querying tasks**:
   - If the user asks for **all tasks**, use "intent": "get_all_tasks".
   - If the user asks about a **specific task**, use "intent": "get_specific_task" and include "task" if identifiable.
   - If the user asks for **all tasks** with a certain status reply with intent as "get_tasks_by_status" and include time if identifiable or description if identifiable or status if identifiable.
   - If the user asks about the **next task**, use "intent": "get_next_task".
5.If the user's command is unclear or does not match any of the above intents, respond with:
   - "intent": "unknown"
**Always respond strictly in JSON** with no additional text.
User command: "{transcript}"
"""
def get_task_intent():
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a JSON-only task manager intent extractor."},
            {"role": "user", "content": prompt.replace("{transcript}", transcript)}
        ],
        "temperature": 0.2
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    result_text = result["choices"][0]["message"]["content"]
    result = json.loads(result_text)
    if result["intent"] == "add_task":
        response = requests.post(
            "http://127.0.0.1:8000/add_task/",
            json={
                "tasks": result.get("task"),
                "time": result.get("time"),
                "description": result.get("description"),
                "status": "pending",
            },
        )
        resllm = response.json()
        if resllm.get("message") == "Task added successfully":
            task_name = result.get("task")
            audio_generator(f"The task {task_name} has been added successfully.")
        else:
            audio_generator("There was an error adding the task.")
    elif result["intent"] == "update_task":
        response = requests.put(
            "http://127.0.0.1:8000/update_task/",
            json={
                "tasks": result.get("task"),
                "time": result.get("time"),
                "description": result.get("description"),
                "status": result.get("status"),
            },
        )
        resllm = response.json()
        if resllm.get("message") == "Task updated successfully":
            audio_generator(f"The task {result.get('task')} has been updated successfully.")
        else:
            audio_generator("There was an error updating the task.")
    elif result["intent"] == "delete_task":
        response = requests.delete(
            "http://127.0.0.1:8000/delete_task/",
            params={"tasks": result.get("task")},
        )
        resllm = response.json()
        if resllm.get("message") == "Task deleted successfully":
            audio_generator(f"The task {result.get('task')} has been deleted successfully.")
        else:
            audio_generator("There was an error deleting the task.")
    elif result["intent"] == "get_all_tasks":
        response = requests.get("http://127.0.0.1:8000/get_all_tasks/")
        resllm = response.json()
        if resllm.get("message") == "No tasks found":
            audio_generator("There are no tasks found.")
        else:
            task_list = []
            for task in resllm.get("tasks", []):
                task_name = task.get("tasks")
                task_time = task.get("time") or "no specific time"
                task_desc = task.get("description") or "no description provided"
                task_status = task.get("status")
                task_str = f"{task_name} at {task_time}, about {task_desc}, and its status is {task_status}."
                task_list.append(task_str)
            tasks_str = " ".join(task_list)
            audio_generator(f"The tasks are as follows: {tasks_str}.")
    elif result["intent"] == "get_specific_task":
        response = requests.get(
            "http://127.0.0.1:8000/get_specific_task/",
            params={"tasks": result.get("task")},
        )
        resllm = response.json()
        if resllm.get("message") == "Task not found":
            audio_generator(f"The task {result.get('task')} is not a valid task.")
        else:
            resllm=resllm["tasks"]
            task_time = resllm.get("time") or "no specific time"
            task_desc = resllm.get("description") or "no specific description"
            task_status = resllm.get("status")
            task_name = resllm.get("tasks")
            str_list = (
                f"The task is {task_name} at {task_time}, about {task_desc}, "
                f"and its status is {task_status}."
            )
            audio_generator(str_list)
    elif result["intent"] == "get_tasks_by_status":
        response = requests.get(
            "http://127.0.0.1:8000/get_tasks_by_status/",
            params={
                "time": result.get("time"),
                "status": result.get("status"),
            },
        )
        resllm = response.json()
        if resllm.get("message") == "Task not found":
            audio_generator("There are no tasks under the status you provided.")
        else:
            task_list = resllm["tasks"]
            tasks_str = ", ".join([task["tasks"] for task in task_list])
            if result.get("time"):
                audio_generator(f"The tasks at {result.get('time')} are as follows: {tasks_str}.")
            elif result.get("status"):
                audio_generator(f"The tasks with status {result.get('status')} are as follows: {tasks_str}.")
    elif result["intent"] == "get_next_task":
        response = requests.get("http://127.0.0.1:8000/get_next_task/")
        resllm = response.json()
        if resllm.get("message") == "No pending tasks":
            audio_generator("There are no pending tasks.")
        else:
            resllm=resllm["tasks"]
            task_time = resllm.get("time") or "no specific time"
            task_desc = resllm.get("description") or "no specific description"
            task_status = resllm.get("status")
            task_name = resllm.get("tasks")
            str_list = (
                f"The next task is {task_name} at {task_time}, about {task_desc}, "
                f"and its status is {task_status}."
            )
            audio_generator(str_list)
    elif result["intent"] == "unknown":
        audio_generator("I'm sorry, I couldn't understand your request. Please try again with a different command.")
get_task_intent()