import sqlite3
import user
from flask import Flask,render_template, request, session, g, redirect, url_for, abort, flash
from contextlib import closing


#configuration
DATABASE = '/tmp/hello.db'
DEBUG = True
SECRET_KEY = '1234'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

def init_db():
	with closing(connect_db()) as db:
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()


@app.route('/', methods=['GET','POST'])
def show_trees():
    return render_template("map.html")

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id

@app.route('/signup', methods=['GET','POST'])
def signup():
	return render_template('signup.html')

@app.route('/show')
def show():
	cur = g.db.execute('select * from plants')
	entries = [dict(title=row[1], text=row[2]) for row in cur.fetchall()]
	return render_template('show.html', entries=entries)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
