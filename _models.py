from sqlalchemy import Column,Integer,String,Text,JSON,Enum
from sqlalchemy.ext.declarative import declarative_base
Base=declarative_base()
class Tasks(Base):
    __tablename__ ="Tasks"
    id=Column(Integer,primary_key=True,autoincrement=True)
    tasks=Column(String(255),nullable=False)
    time=Column(String(255),nullable=True,default=None)
    description=Column(Text,nullable=True,default=None)
    status=Column(Enum('pending','completed'),nullable=False)  