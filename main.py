from fastapi import FastAPI,WebSocket
import _models
from database import engine,Sessionlocal
import redis
import json
import sys
from response import get_response
app=FastAPI()
r=redis.Redis(host="localhost",port=6379,db=0,decode_responses=True)
_models.Base.metadata.create_all(bind=engine)
def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()
def get_multiple_tasks_from_db(db_all, context):
    if not db_all:
        if context == "filtered":
            return "There are no tasks matching your criteria."
        return "You currently have no tasks."
    total_tasks = len(db_all)
    completed = [t for t in db_all if (t.status or "").lower() == "completed"]
    pending = [t for t in db_all if (t.status or "").lower() == "pending"]
    if context == "filtered":
        if len(completed) == total_tasks:
            intro = f"All {total_tasks} of the matching tasks are completed."
        elif len(pending) == total_tasks:
            intro = f"All {total_tasks} of the matching tasks are still pending."
        elif len(completed) == 0 and len(pending) == 0:
            intro = f"There are {total_tasks} matching tasks with unspecified status."
        else:
            intro = f"There are {total_tasks} matching tasks — {len(pending)} pending and {len(completed)} completed."
    else:
        if len(completed) == total_tasks:
            intro = f"All your {total_tasks} tasks are completed. Great job!"
        elif len(pending) == total_tasks:
            intro = f"You have {total_tasks} pending tasks waiting to be done."
        elif len(completed) == 0 and len(pending) == 0:
            intro = f"You have {total_tasks} tasks with unspecified status."
        else:
            intro = f"You have {total_tasks} tasks, including {len(pending)} pending and {len(completed)} completed."
    task_fragments = []
    for task in db_all:
        task_name = task.tasks
        task_time = task.time or "no specific time"
        task_desc = task.description or "no description provided"
        task_status = task.status or "pending"
        fragment = f"{task_name} at {task_time}, about {task_desc}, and its status is {task_status}"
        task_fragments.append(fragment)
    if len(task_fragments) == 1:
        tasks_str = f"The task is {task_fragments[0]}."
    else:
        tasks_str = ", ".join(task_fragments[:-1]) + ", and " + task_fragments[-1] + "."
    return f"{intro} {tasks_str}"
@app.websocket("/ws")
async def websocket_client(websocket: WebSocket):
    await websocket.accept()
    db = next(get_db())
    while True:
        data=await websocket.receive_text()
        db_products=json.loads(data)
        if db_products.get("intent")=="add_task":
            db.add(_models.Tasks(
                tasks=db_products.get("task"),
                time=db_products.get("time"),
                description=db_products.get("description"),
                status="pending"
            ))
            db.commit()
            await websocket.send_json({"message":get_response("add_task",True,db_products.get("task"))})
        elif db_products.get("intent")=="update_task":
            tasks=db_products["task"]
            db_update=db.query(_models.Tasks).filter(_models.Tasks.tasks==tasks).first()
            if db_update:
                db_update.time=db_products.get("time")
                db_update.description=db_products.get("description")
                db_update.status=db_products.get("status")
                db.commit()
                await websocket.send_json({"message":get_response("update_task",True,tasks)})
            else:
                await websocket.send_json({"message":get_response("update_task",False,tasks)})
        elif db_products.get("intent")=="delete_task":
            tasks=db_products["task"]
            db_update=db.query(_models.Tasks).filter(_models.Tasks.tasks==tasks).first()
            if db_update:
                db.delete(db_update)
                db.commit()
                await websocket.send_json({"message":get_response("delete_task",True,db_products.get("task"))})
            else:
                await websocket.send_json({"message":get_response("delete_task",False,db_products.get("task"))})
        elif db_products.get("intent")=="get_all_tasks":
            db_all=db.query(_models.Tasks).all()
            tasks_str=get_multiple_tasks_from_db(db_all,"all")
            await websocket.send_json({"message":tasks_str})
        elif db_products.get("intent")=="get_specific_task":
          tasks=db_products.get("task")
          db_task=r.get(tasks)
          if db_task:
                db_task=json.loads(db_task)
                await websocket.send_json({"message":f"Here's what I found for '{db_task.tasks}': "
                                          f"it's planned for {db_task.time or 'no specific time'}, "
                                          f"about {db_task.description or 'no description provided'}, "
                                          f"and right now its status is {db_task.status}."})
          else:
            db_task=db.query(_models.Tasks).filter(_models.Tasks.tasks==tasks).first()
            if db_task:
                db_dict = {
                     "tasks": db_task.tasks,
                     "time": db_task.time,
                     "description": db_task.description,
                     "status": db_task.status,
                            }
                r.setex(tasks, 3600, json.dumps(db_dict))
                await websocket.send_json({"message":f"Here's what I found for '{db_task.tasks}': "
                                                     f"it's planned for {db_task.time or 'no specific time'}, "
                                                     f"about {db_task.description or 'no description provided'}, "
                                                     f"and right now its status is {db_task.status}."})
            else:
                await websocket.send_json({"message":"The specified task is not a valid task could you rephrase that for me?"})
        elif db_products.get("intent")=="get_tasks_by_status":
            time=db_products.get("time")
            status=db_products.get("status")    
            description=db_products.get("description")
            query=db.query(_models.Tasks)
            if time:
                query=query.filter(_models.Tasks.time==time)
            if status:
                query=query.filter(_models.Tasks.status==status.lower())
            if description:
                query=query.filter(_models.Tasks.description==description.lower())
            db_all=query.all()
            tasks_str = get_multiple_tasks_from_db(db_all, context="filtered")
            if db_all:
                await websocket.send_json({"message": tasks_str})
            else:
                await websocket.send_json({"message": "There are no tasks matching your criteria."})              
        elif db_products.get("intent")=="get_next_task":
            db_task=db.query(_models.Tasks).filter(_models.Tasks.status=="pending").first()
            if db_task:
                await websocket.send_json({"message":f"Up next, you have the task '{db_task.tasks}'. "
                                          f"It's planned for {db_task.time or 'no specific time'}, "
                                          f"and it's about {db_task.description or 'no description provided'}."})
            else:
                await websocket.send_json({"message":"All tasks are completed"})
        elif db_products.get("intent")=="stop":
            await websocket.send_json({"message":"Stopping the task manager assistant. Goodbye!"})
            await websocket.close()
            sys.exit(1)
            break
        elif db_products.get("intent")=="unknown":
           await websocket.send_json({"message": get_response("invalid_input", True)})