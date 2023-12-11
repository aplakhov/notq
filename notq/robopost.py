import datetime
import json
import click
from notq.db import get_db
from notq.blog import do_create_post
from werkzeug.security import generate_password_hash, check_password_hash

def post_one(title, body, creation_time, username, password):
    db = get_db()
    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()
    if not user:
        db.execute(
            "INSERT INTO user (username, password, created) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), creation_time),
        )
        db.commit()
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()
    elif not check_password_hash(user['password'], password):
        raise RuntimeError("Wrong password")
    
    do_create_post(title, body, user, anon=False, paranoid=False, creation_time=creation_time)

def dt(s):
    return datetime.datetime.strptime(s, r'%d-%m-%Y')

@click.command('robopost')
@click.argument('filename')
@click.option('-u', '--user')
@click.option('-p', '--password')
@click.option('-s', '--starting-date')
@click.option('-f', '--daily-frequency', type=int)
def robopost_command(filename, user, password, starting_date, daily_frequency):
    '''Post everything from FILENAME. 1 json per line, expected fields are 'title', 'text'.'''

    creation_time = dt(starting_date)
    if creation_time < dt('01-01-2023') or creation_time > dt('01-01-2030'):
        raise AttributeError("Starting date looks wrong, expected something like '01-11-2023'")
    if daily_frequency <= 0:
        raise AttributeError("daily frequency should be > 0")
    posting_timedelta = datetime.timedelta(seconds=24*3600/daily_frequency)

    with open(filename, encoding='utf=8') as f:
        lines = f.readlines()
    
    for l in lines:
        post = json.loads(l.strip())
        post_one(post['title'], post['body'], creation_time, user, password)
        creation_time += posting_timedelta

    click.echo(f'Posted everything from {filename}.')