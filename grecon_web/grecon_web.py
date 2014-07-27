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

    # validate_on_submit = true if post + validation
    if form.validate_on_submit():
        search = request.form['search']

        # Validate input syntax
        if not ':' in search:
            flash('Syntax error: Search format is field:pattern')
            return render_template('index.html', form=form)

        # Unpack input + validate pattern
        column_name, search_term = search.lower().split(':', 2)
        if not search_term:
            flash('No pattern entered')
            return render_template('index.html', form=form)

        # Find the correct select query
        if column_name:
            if column_name == 'ip':
                cur.execute('SELECT * FROM suspect_ips WHERE ip LIKE ? ORDER BY Date DESC ', ('%'+search_term+'%',))
            elif column_name == 'hostname':
                cur.execute('SELECT * FROM suspect_ips WHERE hostname LIKE ? ORDER BY Date DESC', ('%'+search_term+'%',))
            elif column_name == 'latitude':
                cur.execute('SELECT * FROM suspect_ips WHERE latitude LIKE ? ORDER BY Date DESC', ('%'+search_term+'%',))
            elif column_name == 'longitude':
                cur.execute('SELECT * FROM suspect_ips WHERE longitude LIKE ? ORDER BY Date DESC', ('%'+search_term+'%',))
            elif column_name == 'country':
                cur.execute('SELECT * FROM suspect_ips WHERE country LIKE ? ORDER BY Date DESC', ('%'+search_term+'%',))
            elif column_name == 'date':
                cur.execute('SELECT * FROM suspect_ips WHERE date LIKE ? ORDER BY Date DESC', ('%'+search_term+'%',))
        else:
            flash('Field %s not found' % column_name)
            return render_template('index.html', form=form)

        entries = cur.fetchall()
        if len(entries) == 0:
            flash('No records found matching %s' % search_term)
            return render_template('index.html', form=form)
        else:
            total = len(entries)
            return render_template('index.html', entries=entries, form=form, total=total)
    else:
        cur.execute('SELECT * FROM suspect_ips ORDER BY Date DESC')
        entries = cur.fetchall()
        return render_template('index.html', entries=entries[0:2500], form=form)

def get_dropdowns():
    db = get_db()
    cur = db.cursor()
    cur.execute('select distinct country from suspect_ips;')
    dropdowns = cur.fetchall()
    choices = zip(dropdowns, dropdowns)
    return choices


if __name__ == '__main__':
    app.run(host='0.0.0.0')


