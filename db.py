#!/usr/bin/env python3

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

engine = create_engine('sqlite:///db.sqlite3', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Association(Base):
    __tablename__ = 'association'
    parents_id = Column(Integer, ForeignKey('tasks.id'), primary_key=True)
    id = Column(Integer, ForeignKey('dependencies.id'), primary_key=True)
    dependencies = relationship("Dependencies")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    chat = Column(Integer)
    name = Column(String(50))
    status = Column(String(10))
    description = Column(String(500))
    dependencies = relationship("Association")
    priority = Column(String(10))
    duedate = Column(Date)

    def __repr__(self):
        return "<Task(id={}, chat={}, name='{}', status='{}')>".format(
            self.id, self.chat, self.name, self.status
        )

class Dependencies(Base):
    __tablename__ = 'dependencies'
    id = Column(Integer, primary_key=True)

Base.metadata.create_all(engine)

if __name__ == '__main__':
    pass
