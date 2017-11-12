from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from database_setup import *
 
engine = create_engine('sqlite:///course.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

session.query(Course).delete()
session.query(CourseInstructor).delete()
session.query(User).delete()

user1 = User(name="Bo",
              email="brucepang96@gmail.com",
              picture='http://screenprism.com/assets/img/article/Morty.JPG')
session.add(user1)
session.commit()


course1 = Course(name = "CSE 8A", user=user1)

session.add(course1)
session.commit()


courseInstructor1 = CourseInstructor(
	name = "Christine Alvarado", 
	date = datetime.datetime.now(),
	description = "Great professor",
	course = course1,
	user = user1)

session.add(courseInstructor1)
session.commit()

courseInstructor2 = CourseInstructor(
	name = "Yingjun Cao", 
	date = datetime.datetime.now(),
	description = "Great professor",
	course = course1,
	user = user1)

session.add(courseInstructor2)
session.commit()



course2 = Course(name = "CSE 8B",
	user = user1)

session.add(course2)
session.commit()


courseInstructor3 = CourseInstructor(
	name = "Yingjun Cao", 
	date = datetime.datetime.now(),
	description = "Great professor",
	course = course2,
	user = user1)

session.add(courseInstructor3)
session.commit()



course3 = Course(name = "CSE 11",
	user = user1)

session.add(course3)
session.commit()


courseInstructor4 = CourseInstructor(
	name = "Rick Ord", 
	date = datetime.datetime.now(),
	description = "Great professor",
	course = course3,
	user = user1)

session.add(courseInstructor4)
session.commit()

print "Your database has been populated with some datas"

