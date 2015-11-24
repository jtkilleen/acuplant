import sqlite3
import csv
from flask import Flask,render_template, request, session, g, redirect, url_for, abort, flash
from contextlib import closing
from flask.ext.bcrypt import Bcrypt

#configuration
DATABASE = '/tmp/hello.db'
DEBUG = True
SECRET_KEY = '1234'

app = Flask(__name__)
bcrypt = Bcrypt(app)
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


@app.route('/treedb')
def add_everything():
	cur = g.db.execute('select * from plants')
	plants = [dict(commonname=row[1], sciname=row[2]) for row in cur.fetchall()]
	cur = g.db.execute('select * from plants inner join plantlocation on plants.id=plantlocation.treeid')
	plantlocations = [dict(commonname=row[1], sciname=row[2], latitude=row[4], longitude=row[5]) for row in cur.fetchall()]
	with open('PlantData.csv', "rU") as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			# print(row['TREE_SpeciesCommonName'],row['TREE_SpeciesLatinName'], row['x'], row['y'])
			if row['TREE_SpeciesCommonName'] != '' and row['TREE_SpeciesLatinName'] != '' and dict(commonname=row['TREE_SpeciesCommonName'],sciname=row['TREE_SpeciesLatinName']) not in plants:
				g.db.execute('insert into plants (commonname, sciname) VALUES (?,?)', [row['TREE_SpeciesCommonName'],row['TREE_SpeciesLatinName']])
				g.db.commit()
				plants.append(dict(commonname=row['TREE_SpeciesCommonName'],sciname=row['TREE_SpeciesLatinName']))

			cur2 = g.db.execute('select * from plantlocation where xCoord = ? and yCoord = ?', [row['y'], row['x']])
			
			if len(cur2.fetchall()) == 0:
				if row['TREE_SpeciesCommonName'] != '' and row['TREE_SpeciesLatinName'] != '' and row['x'] != '' and row['y'] != '' and dict(commonname=row['TREE_SpeciesCommonName'],sciname=row['TREE_SpeciesLatinName'],latitude=row['y'], longitude=row['x']) not in plantlocations:
					cur = g.db.execute('select * from plants where commonname = (?)', [row['TREE_SpeciesCommonName']])
					otherplants = [dict(id=a[0]) for a in cur.fetchall()]
					g.db.execute('insert into plantlocation (treeid, xCoord, yCoord) VALUES (?,?,?)',[otherplants[0]['id'],row['y'],row['x']])
					g.db.commit()
					plantlocations.append(dict(commonname=row['TREE_SpeciesCommonName'], sciname=row['TREE_SpeciesLatinName'], latitude=row['y'], longitude=row['x']))

	# print plants
	# print plantlocations
	return redirect(url_for('show'))

@app.route('/', methods=['GET','POST'])
def show_trees():
	if request.method == 'POST':
		# print "FORM"
		# print request.form
		cur = g.db.execute('select * from plantlocation where xCoord = (?) and yCoord = (?)',[request.form['latitude'],request.form['longitude']])
		entries = [dict(id=row[0]) for row in cur.fetchall()]
		if len(entries) == 0:
			cur = g.db.execute('select * from plants where commonname = (?)', [request.form['select']])
			entries = [dict(id=row[0], commonname=row[1], sciname=row[2]) for row in cur.fetchall()][0]
			# print entries['id']
			# print request.form['latitude']
			# print request.form['longitude']
			g.db.execute('insert into plantlocation (treeid, xCoord, yCoord) VALUES (?,?,?)',[entries['id'],request.form['latitude'],request.form['longitude']])
			g.db.commit()
		else:
			print "Tree Already Added"
			cur = g.db.execute('select * from plants where commonname = (?)', [request.form['select']])
			entries = [dict(id=row[0], commonname=row[1], sciname=row[2]) for row in cur.fetchall()][0]
			# print entries['id']
			# print request.form['latitude']
			# print request.form['longitude']
			# print entries[0]
			print request.form
			if 'delete' in request.form:
				print "DELETE"
				g.db.execute('delete from plantlocation where xCoord=? and yCoord=?', [request.form['latitude'],request.form['longitude']])
				g.db.commit()
			else:	
				g.db.execute('update plantlocation set treeid=? where xCoord=? and yCoord=?',[entries['id'],request.form['latitude'],request.form['longitude']])
				g.db.commit()
		return render_template("map.html")
	cur = g.db.execute('select * from plants group by commonname order by commonname')
	entries = [dict(title=row[1], text=row[2]) for row in cur.fetchall()]
	cur = g.db.execute('select * from plants inner join plantlocation on plants.id=plantlocation.treeid')
	plants = [dict(id=row[0], commonname=row[1], sciname=row[2], xCoord=row[4], yCoord=row[5]) for row in cur.fetchall()]
	#print plants
	return render_template("map.html", entries=entries, plants=plants)

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id

@app.route('/add', methods=['GET','POST'])
def add_tree():
	if request.method == 'POST':
		g.db.execute('insert into plants (commonname, sciname) VALUES (?,?)', [request.form['commonname'],request.form['sciname']])
		g.db.commit()
		return redirect(url_for('show'))
	return render_template('add.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
	if request.method == 'POST':
		cur = g.db.execute('select * from users where username = (?)',[request.form['inputEmail']])
		oldpw =  request.form['inputPassword']
		pw = bcrypt.generate_password_hash(oldpw)
		entries = len(cur.fetchall())
		if entries == 0:
			g.db.execute('insert into users (username, password) VALUES (?,?)',[request.form['inputEmail'],pw])
			g.db.commit()
			session['logged_in'] = True
			return redirect(url_for('show_trees'))

		return redirect(url_for('signup'))
	return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
	if request.method == 'POST':
		print request.form
		cur = g.db.execute('select * from users where username = (?)', [request.form['inputEmail']])
		entries = [dict(username=row[1], password=row[2]) for row in cur.fetchall()]
		#bcrypt.generate_password_hash(request.form['inputPassword'])
		print entries, len(entries)
		if len(entries) == 1 and bcrypt.check_password_hash(entries[0]['password'],request.form['inputPassword']):
			session['logged_in'] = True
			return redirect(url_for('show_trees'))
		else:
			return render_template('login.html')
	# pw_hash = bcrypt.generate_password_hash('hunter2')
	# print bcrypt.check_password_hash(pw_hash, 'hunter2') # returns True
	return render_template('login.html')

@app.route('/logout', methods=['GET','POST'])
def logout():
	session.pop('logged_in', None)
	return redirect(url_for('login'))

@app.route('/show')
def show():
	cur = g.db.execute('select * from plants order by commonname')
	entries = [dict(title=row[1], text=row[2]) for row in cur.fetchall()]
	return render_template('show.html', entries=entries)

@app.route('/locations')
def locations():
	cur = g.db.execute('select * from plantlocation')
	entries = [dict(id=row[0], xCoord=row[1], yCoord=row[2]) for row in cur.fetchall()]
	return render_template('locations.html', entries=entries)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
