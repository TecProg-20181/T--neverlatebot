#!/usr/bin/env python3

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import *
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///db.sqlite3', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    chat = Column(Integer)
    name = Column(String)
    status = Column(String)
    dependencies = Column(String)
    parents = Column(String)
    priority = Column(String)
    duedate = Column(Date)

    def __repr__(self):
        return "<Task(id={}, chat={}, name='{}', status='{}')>".format(
            self.id, self.chat, self.name, self.status
        )

Base.metadata.create_all(engine)

if __name__ == '__main__':
    pass
