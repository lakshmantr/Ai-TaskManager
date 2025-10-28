from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
db_url="mysql+mysqlconnector://root:15032009@localhost:3306/aitaskmanager_db"
engine=create_engine(db_url)
Sessionlocal=sessionmaker(bind=engine)