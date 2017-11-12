from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))



class Course(Base):
    __tablename__ = 'course'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="course")

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
       }
 
class CourseInstructor(Base):
    __tablename__ = 'course_instrutor'


    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    date = Column(DateTime, nullable=False)
    description = Column(String(250))
    course_id = Column(Integer,ForeignKey('course.id'))
    course = relationship(Course)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="course_instrutor")

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'date'         : self.date,
           'description'         : self.description,
           'id'         : self.id,
       }



engine = create_engine('sqlite:///course.db')
 

Base.metadata.create_all(engine)
