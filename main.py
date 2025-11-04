from fastapi import FastAPI,WebSocket
import _models
from database import engine,Sessionlocal
import redis
import json
import sys
app=FastAPI()
r=redis.Redis(host="localhost",port=6379,db=0,decode_responses=True)
_models.Base.metadata.create_all(bind=engine)
def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()
def get_multiple_tasks_from_db(db_all):
    task_list=[]
    for task in db_all:
                task_name = task.tasks
                task_time = task.time or "no specific time"
                task_desc = task.description or "no description provided"
                task_status = task.status
                task_str = f"{task_name} at {task_time}, about {task_desc}, and its status is {task_status}."
                task_list.append(task_str)
    tasks_str = " ".join(task_list)
    return tasks_str
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
            await websocket.send_json({"message":f"The task{db_products.get('task')}has been added successfully"})
        elif db_products.get("intent")=="update_task":
            tasks=db_products["task"]
            db_update=db.query(_models.Tasks).filter(_models.Tasks.tasks==tasks).first()
            if db_update:
                db_update.time=db_products.get("time")
                db_update.description=db_products.get("description")
                db_update.status=db_products.get("status")
                db.commit()
                await websocket.send_json({"message":f"The task{db_products.get('task')}has been updated successfully"})
            else:
                await websocket.send_json({"message":f"The task{db_products.get('task')}is not a valid task"})
        elif db_products.get("intent")=="delete_task":
            tasks=db_products["task"]
            db_update=db.query(_models.Tasks).filter(_models.Tasks.tasks==tasks).first()
            if db_update:
                db.delete(db_update)
                db.commit()
                await websocket.send_json({"message":f"The task{db_products.get('task')}has been deleted successfully"})
            else:
                await websocket.send_json({"message":f"The task{db_products.get('task')}is not a valid task"})
        elif db_products.get("intent")=="get_all_tasks":
          db_all=db.query(_models.Tasks).all()
          if db_all:
            tasks_str=get_multiple_tasks_from_db(db_all)
            await websocket.send_json({"message":f"The tasks are as follows{tasks_str}."})
          else:
              await websocket.send_json({"message":"There are no tasks"})
        elif db_products.get("intent")=="get_specific_task":
          tasks=db_products.get("task")
          db_task=r.get(tasks)
          if db_task:
                db_task=json.loads(db_task)
                await websocket.send_json({"message":f"The task is:{db_task.get('tasks')} "f"at {db_task.get('time') or "no specific time"} "f"about {db_task.get('description') or "no specific description"} "f"and it's status is {db_task.get('status')}"})
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
                await websocket.send_json({"message":f"The task is:{db_task.tasks} "f"at {db_task.time or "no specific time"} "f"about {db_task.description or "no specific description"} "f"and it's status is {db_task.status}"})
            else:
                await websocket.send_json({"message":"The specified task is not valid"})
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
            print(db_all)   
            if not db_all:
                await websocket.send_json({"message":"There are no tasks in the specified status"})
            else:
                tasks_str=get_multiple_tasks_from_db(db_all)
                await websocket.send_json({"message":f"The tasks in the specified status are as follows{tasks_str}."})
        elif db_products.get("intent")=="get_next_task":
            db_task=db.query(_models.Tasks).filter(_models.Tasks.status=="pending").first()
            if db_task:
                await websocket.send_json({"message":f"The task is:{db_task.tasks} "f"at {db_task.time or "no specific time"} "f"about {db_task.description or "no description provided"} "f"and it's status is {db_task.status}"})
            else:
                await websocket.send_json({"message":"All tasks are completed"})
        elif db_products.get("intent")=="stop":
            await websocket.send_json({"message":"Stopping the task manager assistant. Goodbye!"})
            await websocket.close()
            sys.exit(1)
            break
        elif db_products.get("intent")=="unknown":
            await websocket.send_json({"message":"I'm sorry, I couldn't understand your request. Please try again with a different command."})