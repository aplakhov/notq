from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from notq.auth import login_required
from notq.db import get_db
from notq.markup import make_html
from notq.data_model import *
from notq.karma import get_user_karma, get_best_users

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    posts = get_top_posts()
    if g.user:
        upvoted, downvoted = get_user_votes_for_posts(g.user['id'])
    else:
        upvoted = downvoted = []
    return render_template('blog/index.html', posts=posts, upvoted=upvoted, downvoted=downvoted)

@bp.route('/new')
def new():
    posts = get_new_posts()
    if g.user:
        upvoted, downvoted = get_user_votes_for_posts(g.user['id'])
    else:
        upvoted = downvoted = []
    return render_template('blog/new.html', posts=posts, upvoted=upvoted, downvoted=downvoted)

def best_title(period):
    if period == "day":
        return 'за день'
    elif period == "week":
        return 'за неделю'
    elif period == "month":
        return 'за месяц'
    elif period == "year":
        return 'за год'
    elif period == "all":
        return 'за всё время'
    else:
        abort(404, f"Unknown time period {period}")

@bp.route('/best/<period>')
def best(period):
    posts = get_best_posts(period)
    if g.user:
        upvoted, downvoted = get_user_votes_for_posts(g.user['id'])
    else:
        upvoted = downvoted = []
    title = 'Лучшие записи ' + best_title(period)
    return render_template('blog/best.html', 
                           besturl=url_for('blog.best', period=period), 
                           posts=posts, 
                           upvoted=upvoted, 
                           downvoted=downvoted,
                           best_title=title)

def add_current_user(users, all_users):
    if not g.user:
        return
    for u in users:
        if g.user['username'] == u[1]:
            return
    for n in range(len(all_users)):
        if all_users[n][0] == g.user['username']:
            users.append((n+1, all_users[n][0], all_users[n][1]))
            return

@bp.route('/best/<period>/users')
def best_users(period):
    title = 'Лучшие пользователи ' + best_title(period)
    all_users = get_best_users(period)
    users = [
        (n+1, all_users[n][0], all_users[n][1])
        for n in range(min(50, len(all_users)))
        if all_users[n][1] >= 0
    ]
    add_current_user(users, all_users)
    return render_template('blog/best_users.html',
                           besturl=url_for('blog.best', period=period),
                           besttype='users',
                           users=users,
                           best_title=title)

@bp.route('/best/<period>/comments')
def best_comments(period):
    title = 'Лучшие комментарии ' + best_title(period)
    comments = get_best_comments(period)
    if g.user:
        cupvoted, cdownvoted = get_user_votes_for_all_comments(g.user['id'])
    else:
        cupvoted = cdownvoted = []
    return render_template('blog/best_comments.html',
                           besturl=url_for('blog.best', period=period),
                           besttype='comments',
                           comments=comments,
                           best_title=title,
                           cupvoted=cupvoted, cdownvoted=cdownvoted)

@bp.route('/u/<username>')
def userpage(username):
    posts = get_user_posts(username)
    if g.user:
        upvoted, downvoted = get_user_votes_for_posts(g.user['id'])
    else:
        upvoted = downvoted = []
    created, nposts, ncomments, banned_until = get_user_stats(username)
    if not created:
        abort(404, f"User {username} doesn't exist.") 
    user = {
        'created': created,
        'karma': get_user_karma(username),
        'nposts': nposts,
        'ncomments': ncomments,
        'banned': banned_until,
        'about': get_about_post(username)['rendered'],
    }
    if g.user and g.user['is_moderator']:
        comments = get_last_user_comments(username)
    else:
        comments = None
    return render_template('blog/userpage.html', user=user, name=username,
                           posts=posts, comments=comments,
                           upvoted=upvoted, downvoted=downvoted)


@bp.route('/u/<username>/ban/<period>')
def ban_user(username, period):
    if not g.user or not g.user['is_moderator']:
        abort(403)
    if period == "day":
        until = datetime.now() + timedelta(days=1)
    elif period == "week":
        until = datetime.now() + timedelta(days=7)
    elif period == "all":
        until = datetime.now() + timedelta(days=99000)
    else:
        abort(404)

    db = get_db()
    db.execute(
                'UPDATE user SET banned_until = ? WHERE username = ?',
                (until, username)
            )
    db.commit()

    flash("User " + username + " was banned until " + until.strftime('%d-%m-%Y %H:%M'))
    return redirect(url_for('blog.userpage', username=username))


@bp.route('/u/<username>/unban')
def unban_user(username):
    if not g.user or not g.user['is_moderator']:
        abort(403)

    db = get_db()
    db.execute(
                'UPDATE user SET banned_until = ? WHERE username = ?',
                (None, username)
            )
    db.commit()

    flash("User " + username + " was unbanned")
    return redirect(url_for('blog.userpage', username=username))


@bp.route('/<int:id>')
def one_post(id):
    posts = get_posts_by_id(id)
    if g.user:
        upvoted, downvoted = get_user_votes_for_posts(g.user['id'])
        cupvoted, cdownvoted = get_user_votes_for_comments(g.user['id'], id)
    else:
        upvoted = downvoted = []
        cupvoted = cdownvoted = []
    return render_template('blog/one_post.html', posts=posts, 
                            upvoted=upvoted, downvoted=downvoted,
                            cupvoted=cupvoted, cdownvoted=cdownvoted)

def check_user_permissions_to_post(db):
    now = datetime.now()

    # 1. is temporarily banned
    if g.user['banned_until'] and g.user['banned_until'] > now:
        return "Вы временно лишены слова и не можете оставлять записи до " + g.user['banned_until'].strftime('%d-%m-%Y %H:%M')
    
    # 2. posts too often
    since = now - timedelta(hours=1)
    count = db.execute('SELECT COUNT(*) AS n FROM post WHERE author_id = ? AND created > ?', (g.user['id'], since)).fetchone()
    if count and count['n'] >= 20:
        return "Вы делаете записи слишком часто. Подождите некоторое время."
    if count and count['n'] >= 4 and not g.user['is_golden'] and get_user_karma(g.user['username']) < 100:
        return "Вы делаете записи слишком часто. Подождите некоторое время."

    return None

def check_post(title, body):
    if not title:
        return 'Нужен заголовок'
    if len(title) > 150:
        return 'Слишком длинный заголовок, уложитесь в 150 символов'
    if not body:
        return 'Нужно что-нибудь написать'
    return None

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        anon = 'authorship' in request.form and request.form['authorship'] == 'anon'
        paranoid = 'authorship' in request.form and request.form['authorship'] == 'paranoid'

        db = get_db()
        error = check_user_permissions_to_post(db)
        if error is None:
            error = check_post(title, body)

        if error is not None:
            flash(error)
        else:
            rendered = make_html(body)
            author_id = g.user['id']
            if paranoid:
                author_id = 1 # Anonymous
                anon = True

            db.execute(
                'INSERT INTO post (title, body, rendered, author_id, anon)'
                ' VALUES (?, ?, ?, ?, ?)',
                (title, body, rendered, author_id, anon)
            )
            db.commit()
            # upvote just created post
            post = db.execute('SELECT id FROM post WHERE author_id = ? ORDER BY created DESC LIMIT 1', (author_id,)).fetchone()
            if post:
                if not paranoid:
                    add_vote(author_id, g.user['is_golden'], post['id'], 2)
                    return redirect(url_for('blog.one_post', id=post['id']))
                else:
                    add_vote(1, False, post['id'], 1)
                    return redirect(url_for('blog.new'))
            else:
                return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post_to_update(id):
    post = get_db().execute(
        'SELECT p.id, title, body, p.created, author_id, username, edited_by_moderator'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if post['edited_by_moderator'] and not g.user['is_moderator']:
        abort(403)

    if post['author_id'] != g.user['id'] and not g.user['is_moderator']:
        abort(403)

    return post

@bp.route('/about', methods=('GET', 'POST'))
@login_required
def about():
    if request.method == 'POST':
        title = "💬 О себе"
        body = request.form['body']
        error = check_post(title, body)

        if error is not None:
            flash(error)
        else:
            rendered = make_html(body)
            author_id = g.user['id']
            db = get_db()
            if not g.user['about_post_id']:
                # create a new post
                db.execute(
                    'INSERT INTO post (title, body, rendered, author_id, show_in_feed)'
                    ' VALUES (?, ?, ?, ?, ?)',
                    (title, body, rendered, author_id, 0)
                )
                # set this post as an "about" post
                post = db.execute('SELECT id FROM post WHERE author_id = ? ORDER BY created DESC LIMIT 1', (author_id,)).fetchone()
                if post:
                    db.execute(
                        'UPDATE user SET about_post_id = ? WHERE id = ?',
                        (post['id'], g.user['id'])
                    )
                    db.commit()
            else:
                # update an old post
                db.execute('UPDATE post SET body = ?, rendered = ? WHERE id = ?', (body, rendered, g.user['about_post_id']))
                db.commit()
            return redirect(url_for('blog.userpage', username=g.user['username']))

    username = None
    if g.user:
        username = g.user['username']
    return render_template('blog/about.html', post=get_about_post(username))

def is_moderator_edit(what):
    return what['author_id'] != g.user['id'] and g.user['is_moderator']

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post_to_update(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = check_post(title, body)

        if error is not None:
            flash(error)
        else:
            rendered = make_html(body)
            if is_moderator_edit(post):
                rendered = "<p class='moderated'>Отредактировано модератором</p>" + rendered
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, rendered = ?, edited = ?, edited_by_moderator = ? WHERE id = ?',
                (title, body, rendered, id, datetime.now(), is_moderator_edit(post))
            )
            db.commit()
            return redirect(url_for('blog.one_post', id=id))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post_to_update(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:post_id>/vote/<int:voteparam>', methods=('POST',))
@login_required
def vote(post_id, voteparam):
    add_vote(g.user['id'], g.user['is_golden'], post_id, voteparam)
    return "1"

@bp.route('/<int:post_id>/votec/<int:comment_id>/<int:voteparam>', methods=('POST',))
@login_required
def voteс(post_id, comment_id, voteparam):
    add_comment_vote(g.user['id'], g.user['is_golden'], post_id, comment_id, voteparam)
    return "1"

def check_user_permissions_to_comment(db):
    now = datetime.now()

    # 1. is temporarily banned
    if g.user['banned_until'] and g.user['banned_until'] > now:
        return "Вы временно лишены слова и не можете комментировать до " + g.user['banned_until'].strftime('%d-%m-%Y %H:%M')
    
    # 2. comments too often
    since = now - timedelta(minutes=5)
    count = db.execute('SELECT COUNT(*) AS n FROM comment WHERE author_id = ? AND created > ?', (g.user['id'], since)).fetchone()
    if count and count['n'] >= 20:
        return "Вы оставляете комментарии слишком часто. Подождите несколько минут."
    if count and count['n'] >= 5 and not g.user['is_golden'] and get_user_karma(g.user['username']) < 100:
        return "Вы оставляете комментарии слишком часто. Подождите несколько минут."

    return None

def check_comment(post_id, text):
    if not post_id:
        return 'Что-то сломалось или вы делаете что-то странное'
    if not text:
        return 'Нужно что-нибудь написать'
    if len(text) > 5000:
        return 'Вы попытались оставить слишком длинный комментарий'
    return None

@bp.route('/addcomment', methods=('POST',))
@login_required
def addcomment():
    post_id = request.form['parentpost']
    text = request.form['text']
    if 'parentcomment' in request.form:
        parent_id = request.form['parentcomment']
        if int(parent_id) <= 0:
            parent_id = None
    else:
        parent_id = None
    anon = 'authorship' in request.form and request.form['authorship'] == 'anon'
    paranoid = 'authorship' in request.form and request.form['authorship'] == 'paranoid'

    db = get_db()
    error = check_user_permissions_to_comment(db)
    if not error:
        error = check_comment(post_id, text)

    if error is not None:
        flash(error)
        return redirect(url_for('blog.one_post', id=post_id))
    else:
        rendered = make_html(text, do_embeds=False)
        author_id = g.user['id']
        if paranoid:
            author_id = 1 # Anonymous
            anon = True
        add_comment(text, rendered, author_id, post_id, parent_id, anon)
        if parent_id:
            anchor = "#answer" + str(parent_id)
        else:
            anchor = "#sendanswer"

        # upvote just created comment
        if not paranoid:
            comment = db.execute('SELECT id FROM comment WHERE author_id = ? ORDER BY created DESC LIMIT 1', (author_id,)).fetchone()
            if comment:
                add_comment_vote(author_id, g.user['is_golden'], post_id, comment['id'], 2)
                anchor = "#answer" + str(comment['id'])
        return redirect(url_for('blog.one_post', id=post_id) + anchor)
