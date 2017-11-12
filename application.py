from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
import datetime
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Course, CourseInstructor, User
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"


#Connect to Database and create database session
engine = create_engine('sqlite:///course.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)




@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    print data
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])

    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id


    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        response = redirect(url_for('showCourses'))
        flash("You are now logged out.")
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


    

#Show all courses with all instructors
@app.route('/')
@app.route('/course')
def showCourses():
  courses = session.query(Course).order_by(asc(Course.name))
  items = session.query(CourseInstructor).order_by(CourseInstructor.date.desc())
  return render_template('courses.html', courses = courses,items = items)


#Show a course's all instructors
@app.route('/course/<path:course_name>/')
def showCourse(course_name):
    courses = session.query(Course).order_by(asc(Course.name))
    course = session.query(Course).filter_by(name = course_name).one()
    items = session.query(CourseInstructor).\
        filter_by(course_id = course.id).all()
    return render_template('course.html', items = items, 
        course = course,courses=courses)
     

#show an instructor item
@app.route('/course/<path:course_name>/<path:courseInstructor_name>')
def showCourseInstructor(course_name,courseInstructor_name):
    courses = session.query(Course).order_by(asc(Course.name))
    course = session.query(Course).filter_by(name = course_name).one()
    item = session.query(CourseInstructor).filter_by(course_id = course.id,
        name = courseInstructor_name).one()
    creator = getUserInfo(item.user_id)
    if 'user_id' not in login_session or creator.id != login_session['user_id']:
        return render_template('publiccourseInstructor.html',course = course,
         item = item,courses=courses)
    else:
        return render_template('courseInstructor.html',course = course, 
            item = item,courses=courses)


#Create a new instructor item
@app.route('/course/new/',methods=['GET','POST'])
def newCourseInstructor():
    if request.method == 'POST':
        newItem = CourseInstructor(
            name = request.form['name'], 
            date = datetime.datetime.now(),
            description = request.form['description'], 
            course = session.query(Course).\
                filter_by(name = request.form['course']).one(),
            user_id=login_session['user_id']
        )
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showCourse', course_name = request.form['course']))
    else:
        courses = session.query(Course).order_by(asc(Course.name))
        return render_template('newCourseInstructor.html',courses=courses)

#Edit a instructor item
@app.route('/course/<path:course_name>/<path:courseInstructor_name>/edit', 
    methods=['GET','POST'])
def editCourseInstructor(course_name, courseInstructor_name):
    courses = session.query(Course).order_by(asc(Course.name))
    course = session.query(Course).filter_by(name = course_name).one()
    editedItem = session.query(CourseInstructor).\
        filter_by(course_id = course.id,name = courseInstructor_name).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['course']:
            c = session.query(Course).filter_by(name = request.form['course']).one()
            editedItem.course = c
        session.add(editedItem)
        session.commit() 
        flash('Course Instructor Successfully Edited')
        return redirect(url_for('showCourse', course_name = editedItem.course.name))
    else:
        return render_template('editCourseInstructor.html', 
            courses = courses, course = course, item = editedItem)


#Delete a instructor item
@app.route('/restaurant/<path:course_name>/<path:courseInstructor_name>/delete',
     methods = ['GET','POST'])
def deleteCourseInstructor(course_name,courseInstructor_name):
    course = session.query(Course).filter_by(name = course_name).one()
    itemToDelete = session.query(CourseInstructor).filter_by(course_id = 
        course.id,name = courseInstructor_name).one()    
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Course Instructor Successfully Deleted')
        return redirect(url_for('showCourse', course_name = course_name))
    else:
        return render_template('deleteCourseInstructor.html', course = 
            course, item = itemToDelete)


@app.route('/catalog.json')
def jsonAPI():
    courses = session.query(Course).all()
    courses_dict = [c.serialize for c in courses]
    for c in range(len(courses_dict)):
        items = [i.serialize for i in session.query(CourseInstructor)\
                    .filter_by(course_id=courses_dict[c]["id"]).all()]
        if items:
            courses_dict[c]["Course Instructor"] = items

    return jsonify(Category=courses_dict)



if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
