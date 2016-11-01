"""
    Name My Cat!

    A website for naming your new pet cat!

    We store a database of potential cat names, and return one every time a user
    hits our site.

    We've also got an admin interface for adding and removing potential cat names
    from the database.
"""

import os
import sys
import psycopg2

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

app = Flask(__name__)

# Load app config
# Overwrite config with environment variables if set
app.config.update(dict(
    PG_HOST=os.getenv("PG_HOST", '127.0.0.1'),
    PG_PORT=os.getenv("PG_PORT", '5432'),
    PG_DB=os.getenv("PG_DB", 'namemycat'),
    PG_USER=os.getenv("PG_USER", 'namemycat'),
    PG_PASS=os.getenv("PG_PASS", 'namemycat'),
    DEBUG=os.getenv("FLASK_DEBUG", True),
))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)
app.secret_key = os.getenv("APP_SECRET", 'suchsecrets')


def connect_db():
    """
    Connects to the specific database.
    """

    db = psycopg2.connect(
        "dbname={dbname} host={host} port={port} user={user} password={passwd}".format(
            dbname=app.config['PG_DB'],
            host=app.config['PG_HOST'],
            port=app.config['PG_PORT'],
            user=app.config['PG_USER'],
            passwd=app.config['PG_PASS']
        )
    )

    db.autocommit = True

    return db


def init_db():
    """
    Create the db from a sql schema
    """
    db = get_db()

    cur = db.cursor()

    resp = False

    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS names(
              id SERIAL PRIMARY KEY,
              name text
            );
            """
        )
        resp = True
    except psycopg2.ProgrammingError as e:
        print("Error: {e}".format(e=e))

    cur.close()

    return resp


@app.cli.command('initdb')
def initdb_command():
    """
    Command invoked from the shell to generate the required
    DB
    """
    if init_db():
        print('Initialized the database.')
        sys.exit(0)
    else:
        print('Unable to initialize the database.')
        sys.exit(1)


def get_db():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db'):
        g.db = connect_db()

    return g.db


def get_random_name():
    """
    Select a single, random row from the names table as a string
    or False.
    """
    db = get_db()

    cur = db.cursor()
    resp = False

    cur.execute("SELECT name FROM names ORDER BY random() LIMIT 1;")

    if cur.rowcount > 0:
        resp = cur.fetchone()[0]

    cur.close()

    return resp


def submit_cat_name(name):
    """
        Attempt to add a new name to the database.
        Return True on success and False on failure.
    """
    db = get_db()
    cur = db.cursor()
    resp = False

    if len(name) > 0:
        try:
            cur.execute('INSERT INTO names (name) VALUES (%s)', [name])
            resp = True
        except Exception as e:
            print(e)

    cur.close()

    return resp


@app.teardown_appcontext
def close_db(error):
    """
    Cose the DB connection at the end of the request
    """
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/', methods=['GET', 'POST'])
def home():
    """
        Get a random pet name from our database, or default to "cat" is we haven't
        added any yet.
    """

    if request.method == 'GET':

        name = get_random_name()

        if name is False:
            name = "Cat"

        return render_template('home.html', name=name.title())
    else:
        if submit_cat_name(request.form['name']):
            flash('Thanks, Your cat name has been submitted!')
        else:
            flash("Sorry, Something went wrong when adding your name!")

        return redirect(url_for('home'))


if __name__ == "__main__":
    app.run()
