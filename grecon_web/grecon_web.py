import os
import sqlite3
from forms import SearchForm
#from flask.ext.wtf import Form
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'suspect_ips.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('GRECON_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/', methods=('POST', 'GET'))
def home():
    form = SearchForm()
    db = get_db()
    cur = db.cursor()

    #if request.method == 'POST' and form.validate():
    if form.validate_on_submit():
        country = request.form['country']
        sql_query = ('SELECT * FROM suspect_ips WHERE country = ? COLLATE NOCASE')
        cur.execute(sql_query, (country,))
        entries = cur.fetchall()
        if len(entries) == 0:
            #error = 'No records found'
            flash('No records found')
            return render_template('index.html', form=form)
        return render_template('index.html', entries=entries, form=form)
    else:
        cur.execute('select * from suspect_ips')
        entries = cur.fetchall()
        return render_template('index.html', entries=entries, form=form)

if __name__ == '__main__':
    app.run(host='0.0.0.0')


