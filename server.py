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
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, session, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

#
# The following uses the postgresql test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# Swap out the URI below with the URI for the database created in part 2
DATABASEURI = "postgresql://rd2704:v4d8a@104.196.175.120/postgres"


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

#engine.execute("""DROP TABLE IF EXISTS test;""")

# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
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
@app.route('/', methods=['POST', 'GET'])
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  #
  # example of a database query
  #
  currentUid = ''
  currentUidMessage = 'Not logged in yet!'
  if 'uid' in session:
    currentUid = session['uid']
    currentUidMessage = 'Logged in as ' + currentUid
  cursor = g.conn.execute("SELECT * FROM Categories")
  categories = []
  for result in cursor:
    categories.append({'name' :result[1], 'id': result[0]})  # can also be accessed using result[0]

  cursor = g.conn.execute("SELECT * FROM PaymentInfo Where uid = %s", currentUid)
  paymentList = []
  for result in cursor:
    paymentList.append({'paymentId' :result[1], 'accountNo': result[2], 'billingAddress': result[3]})  # can also be accessed using result[0]
  
  cursor = g.conn.execute("SELECT * FROM Shippers")
  shippers = []
  for result in cursor:
    shippers.append({'shipperId' :result[0], 'phone': result[1], 'company': result[2]}) 

  cursor = g.conn.execute("SELECT O.orderId, S.company, V.name FROM Orders AS O, Shippers AS S, Vehicle_supply AS V WHERE O.uid = %s AND O.shipperId=S.shipperId AND O.vid=V.vid", currentUid)
  orders = []
  for result in cursor:
    orders.append({'orderId' :result[0], 'shipper': result[1], 'vehicle': result[2]}) 
  
  vehicleList = []
  selectedCategory = ''
  if request.method == "POST":
    cursor = g.conn.execute("SELECT name FROM Categories WHERE categoryId = %s", request.form["categories"])
    for result in cursor:
      selectedCategory = result[0]
      vehicles = g.conn.execute("SELECT * FROM Vehicle_supply where vid in(SELECT vid FROM VehiclesBelongs where categoryId= %s)", request.form["categories"])
      for i in vehicles:
        reviewDBresult = g.conn.execute('SELECT uid, content FROM CustomerReveiws where vid = %s', i[0])
        reviewList = []
        for j in reviewDBresult:
          reviewList.append({'uid': j[0], 'content': j[1]})
        vehicleList.append({'name': i[2], 'picture': i[3], 'description': i[4],
          'unitInStock': i[5], 'price': i[6], 'discount': i[7], 'vid': i[0], 'reviewList': reviewList})

  cursor.close()
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
  context = dict(categories = categories, selectedCategory = selectedCategory, vehicleList = vehicleList, 
    currentUid = currentUid, currentUidMessage = currentUidMessage, paymentList = paymentList, 
    shippers = shippers, orders = orders)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

@app.route('/signup', methods=['POST'])
def signup():
  uid = request.form['uid']
  name = request.form['name']
  address = request.form['address']
  phone = request.form['phone']
  email = request.form['email']
  role = request.form['role']
  g.conn.execute('INSERT into Users (uid, name, address, phone, email) VALUES (%s, %s, %s, %s, %s)', 
    (uid, name, address, phone, email))
  if role == 'customer':
    g.conn.execute('INSERT into Customers VALUES (%s);', (uid))
  elif role == 'supplier':
    g.conn.execute('INSERT into Suppliers VALUES (%s);', (uid))

  return redirect('/')


#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#

@app.route('/writereview', methods = ['POST'])
def writereview():
  import time
  timestamp = int(time.time())
  vid = request.form['vid']
  content = request.form['content']
  uid = session['uid']
  reviewId = 'r' + str(timestamp)
  g.conn.execute('INSERT into CustomerReveiws VALUES (%s, %s, %s, %s)', 
    vid, uid, reviewId, content)
  return redirect('/')

@app.route('/buynow', methods = ['POST'])
def buynow():
  import time
  timestamp = int(time.time())
  if request.form['accountNo'] != '' and request.form['billingAddress']!= '':
    paymentId = 'p' + str(timestamp)
    g.conn.execute('INSERT into PaymentInfo VALUES (%s, %s, %s, %s)', 
      session['uid'], paymentId, request.form['accountNo'], request.form['billingAddress'])
  else:
    paymentId = request.form['paymentId']
  orderId = 'o' + str(timestamp)
  shipperId = request.form['shipperId']
  vid = request.form['vid']
  uid = session['uid']
  
  # requiredDate
  # shippingDate
  g.conn.execute('INSERT into Orders (orderId, shipperId, vid, uid, paymentId) VALUES (%s, %s, %s, %s, %s)', 
    orderId, shipperId, vid, uid, paymentId)
  #print shipperId, vid, uid, paymentId
  return redirect('/')

@app.route('/addvehicle', methods = ['POST'])
def addvehicle():
  import time
  timestamp = int(time.time())
  name = request.form['name']
  picture = request.form['picture']
  description = request.form['description']
  unitInStock = request.form['unitInStock']
  price = request.form['price']
  discount = request.form['discount']
  categories = request.form['categories']
  vid = 'v' + str(timestamp)
  uid = session['uid']
  g.conn.execute('INSERT into Vehicle_supply VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', 
    vid, uid, name, picture, description, unitInStock, price, discount)
  g.conn.execute('INSERT into VehiclesBelongs VALUES (%s, %s)', vid, categories)
  return redirect('/')


@app.route('/login', methods = ['POST'])
def login():
  result = g.conn.execute('SELECT * from Users Where uid=%s', request.form['uid'])
  authenticated = 0
  for i in result:
    authenticated = 1
  if authenticated == 1:
    session['uid'] = request.form['uid']
  return redirect('/')

@app.route('/logout')
def logout():
  session.pop('uid', None)
  return redirect('/')


@app.route('/another')
def another():
  return render_template("anotherfile.html")


# Example of adding new data to the database
# @app.route('/add', methods=['POST'])
# def add():
#   name = request.form['name']
#   print name
#   cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
#   g.conn.execute(text(cmd), name1 = name, name2 = name);
#   return redirect('/')


# @app.route('/login')
# def login():
#     abort(401)
#     this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='127.0.0.1')
  @click.argument('PORT', default=5000, type=int)
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
