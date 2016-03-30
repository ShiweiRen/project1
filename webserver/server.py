#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from dateutil.parser import parse
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, session, url_for, flash, request, render_template, g, redirect, Response
from contextlib import closing
DEBUG = True
SECRET_KEY = 'development key'

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config.from_object(__name__)

#
# The following uses the sqlite3 database test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@w4111db.eastus.cloudapp.azure.com/username
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@w4111db.eastus.cloudapp.azure.com/ewu2493"
#
DATABASEURI = "postgresql://sr3254:DMNSLM@w4111db.eastus.cloudapp.azure.com/sr3254"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/', methods=['POST','GET'])
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT * FROM movies")

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  movies = [dict(movie_name=row["movie_name"],rating=row["rating"],mid=row["mid"]) for row in cursor.fetchall()]
  cursor.close()

  cursor = g.conn.execute("SELECT * FROM theatres")
  theatres = [dict(theatre_name=row["theatre_name"],thid=row["thid"]) for row in cursor.fetchall()]
  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", movies=movies,theatres=theatres)



@app.route('/gotomovie', methods=['GET','POST'])
def gotomovie():
  session['movie'] = request.form['movie']
  #render_template("movie.html",movie=movie)
  return redirect('/movie')

@app.route('/gototheatre', methods=['GET','POST'])
def gototheatre():
  session['theatre'] =request.form['theatre']
  return redirect('/theatre')

@app.route('/movie',methods=['POST','GET'])
def movie():
  if not session.has_key('movie') or session['movie']==None:
    return redirect('/')
  cursor = g.conn.execute("SELECT t.thid,theatre_name,m.mid,hid,start_time,end_time,available_seats,price FROM play_at p,movies m,theatres t WHERE p.mid=m.mid and p.thid=t.thid and movie_name='%s'"%session['movie'])
  info = [dict(mid=row["mid"],start_time=row["start_time"],end_time=row["end_time"],hid=row["hid"],thid=row["thid"],price=row["price"],theatre_name=row["theatre_name"],available_seats=row["available_seats"]) for row in cursor.fetchall()]
  cursor.close()
  return render_template("movie.html",info=info)

@app.route('/theatre',methods=['POST','GET'])
def theatre():
  if not session.has_key('theatre') or session['theatre']==None:
    return redirect('/')
  cursor = g.conn.execute("SELECT t.thid,theatre_name,m.mid,movie_name,hid,start_time,end_time,available_seats,price FROM play_at p,movies m,theatres t WHERE p.mid=m.mid and p.thid=t.thid and theatre_name='%s'"%session['theatre'])
  info = [dict(mid=row["mid"],start_time=row["start_time"],end_time=row["end_time"],hid=row["hid"],thid=row["thid"],price=row["price"],movie_name=row["movie_name"],theatre_name=session['theatre'],available_seats=row["available_seats"]) for row in cursor.fetchall()]
  cursor.close()
  return render_template("theatre.html",info=info)

@app.route('/backfrommovie')
def backfrommovie():
  session.pop('movie',None)
  return redirect('/')

@app.route('/backfromtheatre')
def backfromtheatre():
  session.pop('theatre',None)
  return redirect('/')


@app.route('/order',methods=['POST','GET'])
def order():
  if 'logged_in' not in session:
    return redirect('/login')
  if session['logged_in']==True:
    movie_name = request.form["movie_name"]
    cursor = g.conn.execute("SELECT mid FROM movies WHERE movie_name='%s'" % movie_name)
    mid = (cursor.fetchall())[0][0]
    theatre_name = request.form["theatre_name"]
    cursor = g.conn.execute("SELECT thid FROM theatres WHERE theatre_name='%s'" % theatre_name)
    thid = (cursor.fetchall())[0][0]
    hid = request.form["hid"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    available_seats = request.form["available_seats"]
    if available_seats ==0:
        return redirect('/')
    available_seats = int(available_seats)-1
    price = request.form["price"]
    info = [dict(movie_name=movie_name, theatre_name=theatre_name, hid=hid, start_time=start_time, end_time=end_time, available_seats=available_seats, price=price)]
    email = session["username"]
    cursor = g.conn.execute("SELECT uid FROM users WHERE email = '%s'" % email)
    uid = (cursor.fetchall())[0][0]
    g.conn.execute("INSERT INTO orders VALUES ('%s')" % uid)
    g.conn.execute("INSERT INTO tickets (type, status, mid, start_time, end_time, hid, thid) VALUES ('%s','%s',%s,'%s','%s',%s,%s)"\
      % ('student', 'complete', mid, start_time, end_time, hid, thid))
    cursor = g.conn.execute("SELECT last_value FROM oid_seq")
    oid = (cursor.fetchall())[0][0]
    cursor = g.conn.execute("SELECT last_value FROM tid_seq")
    tid = (cursor.fetchall())[0][0]
    g.conn.execute("INSERT INTO order_includes VALUES (%s, %s)" % (oid, tid))
    g.conn.execute("update play_at set available_seats = available_seats - 1 where mid=%s and start_time='%s' and hid=%s and thid=%s"%(mid,start_time,hid,thid))
    return render_template("order.html",info=info)

@app.route('/delete',methods=['POST','GET'])
def delete():
  oid = request.form["oid"]
  cursor = g.conn.execute("SELECT tid FROM order_includes WHERE oid=%s" % oid)
  tid = (cursor.fetchall())[0][0]
  g.conn.execute("DELETE FROM order_includes WHERE oid=%s or tid=%s" % (oid,tid))
  g.conn.execute("DELETE FROM orders WHERE oid=%s" % oid)
  g.conn.execute("DELETE FROM tickets WHERE tid=%s" % tid)
  return redirect('/history')

@app.route('/history',methods=['POST','GET'])
def history():
  email = session["username"]
  cursor = g.conn.execute("SELECT uid FROM users WHERE email = '%s'" % email)
  uid = (cursor.fetchall())[0][0]
  cursor = g.conn.execute("SELECT o.uid, o.oid, o.order_time, o.discount, t.start_time, t.hid, th.theatre_name, m.movie_name \
    FROM orders o, order_includes oi, tickets t, theatres th, movies m \
    WHERE o.uid=%s and o.oid=oi.oid and t.tid=oi.tid and t.thid=th.thid and m.mid=t.mid" % uid)
  info = [dict(uid=row["uid"], oid=row["oid"], time=row["order_time"], discount=row["discount"], start_time=row["start_time"],\
    theatre_name=row["theatre_name"], hid=row["hid"], order_time=row["order_time"], movie_name=row["movie_name"]) for row in cursor.fetchall()]
  return render_template("history.html",info=info)

@app.route('/search', methods=['POST','GET'])
def search():
  info=[]
  if request.method == "POST":
    mname="%%"
    thname="%%"
    date=request.form['date']
    if request.form["movie_name"]=="" and request.form["theatre_name"]=="" and request.form["date"]=="":
      return render_template("search.html",info=info)
    if request.form["movie_name"]!="":
      mname=request.form["movie_name"]
    if request.form["theatre_name"]!="":
      thname=request.form["theatre_name"]
    if date=="":
      cursor = g.conn.execute("SELECT t.thid,theatre_name,m.mid,movie_name,hid,start_time,end_time,available_seats,price FROM play_at p,movies m,theatres t WHERE p.mid=m.mid and p.thid=t.thid and lower(theatre_name) like lower('%s') and lower(movie_name) like lower('%s')"%(thname,mname))
    else:
      if not is_valid_date(date):
        error = "Not valid date"
        return render_template("search.html",info = info ,error = error)
      else:
        cursor = g.conn.execute("SELECT t.thid,theatre_name,m.mid,movie_name,hid,start_time,end_time,available_seats,price FROM play_at p,movies m,theatres t WHERE p.mid=m.mid and p.thid=t.thid and lower(theatre_name) like lower('%s') and lower(movie_name) like lower('%s') and date(start_time)='%s'"%(thname,mname,date))
    info = [dict(mid=row["mid"],start_time=row["start_time"],end_time=row["end_time"],hid=row["hid"],thid=row["thid"],price=row["price"],movie_name=row["movie_name"],theatre_name=row["theatre_name"],available_seats=row["available_seats"]) for row in cursor.fetchall()]
    cursor.close()
    return render_template("search.html",info=info)
  return render_template("search.html",info=info)

def is_valid_date(str):
  try:
    #parse(str, "%Y-%m-%d")
    parse(str)
    return True
  except ValueError:
    return False

@app.route('/signup', methods=['POST','GET'])
def signup():
  error = None
  if session.has_key('logged_in') and session['logged_in']:
    return redirect('/')
  if request.method == "POST":
    cur = g.conn.execute("select count(*) from users where email='%s'"%(request.form['email']))
    result = cur.fetchall()
    if result[0][0]!=0:
      error = 'That email has already been used'
    elif request.form['password']!=request.form['password2']:
      error = 'Password do not match.'
    elif len(request.form['credit_card_no']) != 16:
        error = 'Invalid credit card number!'
    else:
      cur = g.conn.execute("insert into users(email,credit_card_no,password) values('%s','%s','%s')"%(request.form['email'],request.form['credit_card_no'],request.form['password']))
      session['logged_in'] = True
      session["username"] = request.form['email']
      flash('You have signed up successfully.')
    return redirect('/')
  return render_template('signup.html',error=error)

@app.route('/login', methods=['POST','GET'])
def login():
    error = None
    if request.method == 'POST':
      cur = g.conn.execute("select count(*) from users where email= '%s' and password='%s'"%(request.form['username'],request.form['password']))
      result = cur.fetchall()
      if result[0][0]==0:
        error = 'Invalid username or password'
      else:
        session['logged_in'] = True
        session["username"] = request.form['username']
        flash('You have logged in as '+request.form['username'])
        return redirect('/')
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop("username",None)
    flash('You were logged out')
    return redirect(url_for('index'))


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
