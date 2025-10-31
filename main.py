from fastapi import FastAPI,Depends
import _models
from sqlalchemy.orm import Session
from database import engine,Sessionlocal
from pydantic import BaseModel
import redis
import json
app=FastAPI()
r=redis.Redis(host="localhost",port=6379,db=0,decode_responses=True)
_models.Base.metadata.create_all(bind=engine)
class TaskRequestValidation(BaseModel):
    id:int|None=None
    tasks:str
    time:str|None=None
    description:str|None=None
    status:str|None=None
    class Config:
        orm_mode = True
def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()
@app.post("/add_task/")
def add_task(task:TaskRequestValidation,db:Session=Depends(get_db)):
    db.add(_models.Tasks(**task.model_dump()))
    db.commit()
    return {"message":"Task added successfully"}
@app.put("/update_task/")
def update_task(task: TaskRequestValidation, db: Session = Depends(get_db)):
    db_task = db.query(_models.Tasks).filter(_models.Tasks.tasks== task.tasks).first()
    if not db_task:
        return {"message":"Invalid Request"}
    for key, value in task.model_dump().items():
        if value is not None:
            setattr(db_task, key, value)
    db.commit()
    return {"message":"Task updated successfully"}
@app.delete("/delete_task/")
def delete_task(tasks:str,db:Session=Depends(get_db)):
    db_products=db.query(_models.Tasks).filter(_models.Tasks.tasks==tasks).first()
    if db_products:
        db.delete(db_products)
        db.commit()
        return {"message":"Task deleted successfully"}
    else:
        return {"message":"Invalid Request"}
@app.get("/get_all_tasks/")
def get_all_tasks(db: Session = Depends(get_db)):
    tasks = db.query(_models.Tasks).all()
    if not tasks:
        return {"message":"No tasks found","tasks":[]}
    formatted_tasks = [
        {
            "tasks": task.tasks,
            "time": task.time,
            "description": task.description,
            "status": task.status
        }
        for task in tasks
    ]
    return {"message": "Tasks retrieved successfully", "tasks": formatted_tasks}
@app.get("/get_next_task/")
def get_next_task(db: Session = Depends(get_db)):
    task = db.query(_models.Tasks).filter(_models.Tasks.status == 'pending').first()  
    if not task:
        return {"message": "No pending tasks", "tasks": []}  
    formatted_task = {
        "tasks": task.tasks,
        "time": task.time,
        "description": task.description,
        "status": task.status
    }
    return {"message": "Next task found", "tasks":formatted_task}
@app.get("/get_specific_task/")
def get_specific_task(tasks:str,db:Session=Depends(get_db)):
    cached_task = r.get(tasks)
    if cached_task:
        return {"message":"Task Found","tasks":json.loads(cached_task)}
    task=db.query(_models.Tasks).filter(_models.Tasks.tasks==tasks).first()
    if not task:
        return {"message":"Task not found","tasks":[]}
    else:
        formatted_task={
            "tasks":task.tasks,
            "time":task.time,
            "description":task.description,
            "status":task.status
        }
        r.set(tasks,json.dumps(formatted_task))
        return{"message":"Task Found","tasks":formatted_task}
@app.get("/get_tasks_by_status/")
def task_by_status(time:str|None=None,
                   status:str|None=None,
                   db:Session=Depends(get_db)):
    query=db.query(_models.Tasks)
    if time:
        query=query.filter(_models.Tasks.time==time)
    if status:
        query=query.filter(_models.Tasks.status==status)
    tasks=query.all()
    if not tasks:
        return {"message":"Tasks not found","tasks":[]}
    else:
        formatted_tasks=[{
            "tasks":task.tasks,
            "time":task.time,
            "description":task.description,
            "status":task.status
        }
        for task in tasks
        ]
        return {"message":"Tasks found in the specified status","tasks":formatted_tasks}