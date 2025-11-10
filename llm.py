import requests
import websockets
import asyncio
from stt import get_user_input
import json
from tts import audio_generator
import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FASTAPI_WS_URL = "ws://127.0.0.1:8000/ws"
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
3. If the user is deleting a task, include:
   - "intent": "delete_task"
   - "task": the task being deleted
   - "time": the scheduled time (if known)
4. If the user is **querying tasks**:
   - If the user question is to get all the tasks in database use "intent": "get_all_tasks".
   - If the user asks about a **specific task**, use "intent": "get_specific_task" and include "task" if identifiable.
   - If the user asks for **all tasks** with a certain status reply with intent as "get_tasks_by_status" and include time if identifiable or description if identifiable or status if identifiable(completed or pending) and do not include task name.
   - If the user asks about the **next task**, use "intent": "get_next_task".
5.If the user's command is unclear or does not match any of the above intents, respond with:
   - "intent": "unknown"
6.If the user's command is to stop,respond with:
   - "intent":"stop"
**Always respond strictly in JSON** with no additional text.
User command: "{transcript}"
"""
def get_task_intent(transcript):
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
    return result_text
async def websocket_client():
    async with websockets.connect(FASTAPI_WS_URL,ping_interval=120,ping_timeout=20) as websocket:
        while True:
            user_input=await asyncio.to_thread(get_user_input)
            result=await asyncio.to_thread(get_task_intent,user_input)
            print(result)
            await websocket.send(result)
            response = await websocket.recv()
            response=json.loads(response)
            message=response.get("message")
            await asyncio.to_thread(audio_generator,message)
            if message=="Stopping the task manager assistant. Goodbye!":
                break
if __name__ == "__main__":
    asyncio.run(websocket_client())