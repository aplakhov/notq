from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from notq.auth import login_required
from notq.autocut import autocut
from notq.db import get_db
from notq.markup import make_html
from notq.data_model import *
from notq.karma import get_user_karma, get_best_users
from notq.constants import *

bp = Blueprint('blog', __name__)

def posts_list_with_pager(template_name, all_posts, page, pageurl, **kwargs):
    if g.user:
        upvoted, downvoted = get_user_votes_for_posts(g.user['id'])
    else:
        upvoted = downvoted = []
    start = page * POST_FEED_PAGE_SIZE
    if start >= len(all_posts):
        posts = []
    else:
        posts = all_posts[start : start + POST_FEED_PAGE_SIZE]
    pager = {
        'numpages': (len(all_posts) + POST_FEED_PAGE_SIZE - 1) // POST_FEED_PAGE_SIZE,
        'page': page,
        'pageurl': pageurl
    }
    return render_template(template_name, posts=posts, pager=pager, upvoted=upvoted, downvoted=downvoted, **kwargs)

@bp.route('/', defaults={'page': 0})
@bp.route('/page/<int:page>')
def index(page):
    return posts_list_with_pager('blog/index.html', get_top_posts(), page, '/page/')

@bp.route('/new', defaults={'page': 0})
@bp.route('/new/page/<int:page>')
def new(page):
    return posts_list_with_pager('blog/new.html', get_new_posts(), page, '/new/page/')

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

@bp.route('/best/<period>', defaults={'page': 0})
@bp.route('/best/<period>/page/<int:page>')
def best(period, page):
    title = 'Лучшие записи ' + best_title(period)
    return posts_list_with_pager('blog/best.html', get_best_posts(period), page, f'/best/{period}/page/', 
                                 besturl=url_for('blog.best', period=period), best_title=title)

@bp.route('/tag/<tagname>', defaults={'page': 0})
@bp.route('/tag/<tagname>/page/<int:page>')
def tagpage(tagname, page):
    return posts_list_with_pager('blog/tag.html', get_tag_posts(tagname), page, f'/tag/{tagname}/page/', tagname=tagname)

def add_current_user(users, all_users):
    if not g.user:
        return
    for u in users:
        if g.user['username'] == u['username']:
            return
    for u in all_users:
        if g.user['username'] == u['username']:
            users.append(u)
            return

@bp.route('/best/<period>/users')
def best_users(period):
    title = 'Лучшие пользователи ' + best_title(period)
    all_users = get_best_users(period)
    users = all_users[:100]
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

@bp.route('/u/<username>', defaults={'page': 0})
@bp.route('/u/<username>/page/<int:page>')
def userpage(username, page):
    if username == "anonymous" and g.user and g.user['is_moderator']:
        posts = get_anon_posts()
    else:
        posts = get_user_posts(username)

    if g.user and g.user['is_moderator']:
        comments = get_last_user_comments(username)
    else:
        comments = None

    created, nposts, ncomments, banned_until, is_golden = get_user_stats(username)
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

    return posts_list_with_pager('blog/userpage.html', posts, page, f'/u/{username}/page/', 
                                 user=user, name=username, comments=comments, black_logo=is_golden)

def do_ban_user(until, username):
    db = get_db()
    db.execute(
                'UPDATE user SET banned_until = ? WHERE username = ?',
                (until, username)
            )
    db.commit()

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
    do_ban_user(until, username)
    flash("User " + username + " was banned until " + until.strftime('%d-%m-%Y %H:%M'))
    return redirect(url_for('blog.userpage', username=username))


@bp.route('/u/<username>/delete/<period>')
def delete_user(username, period):
    if not g.user or not g.user['is_moderator']:
        abort(403)

    message = "User " + username + "'s comments were removed"
    if period == "day":
        since = datetime.now() - timedelta(days=1)
    elif period == "week":
        since = datetime.now() - timedelta(days=7)
    elif period == "all":
        since = datetime.now() - timedelta(days=10000)
        do_ban_user(datetime.now() + timedelta(days=99000), username)
        delete_user_posts(username)
        message = "User " + username + " and all their comments and posts were removed, and the user was banned"
    else:
        abort(404)

    delete_user_comments(since, username)

    flash(message)
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


@bp.route('/<int:id>', defaults={'page': 0})
@bp.route('/<int:id>/page/<int:page>')
def one_post(id, page):
    posts = get_posts_by_id(id)
    if not posts:
        abort(404, "Post doesn't exits")
    if g.user:
        upvoted, downvoted = get_user_votes_for_posts(g.user['id'])
        cupvoted, cdownvoted = get_user_votes_for_comments(g.user['id'], id)
    else:
        upvoted = downvoted = []
        cupvoted = cdownvoted = []
    pager = {
        'page': page,
        'numpages': 1
    }
    comments = posts[0]['comments']
    if comments:
        pager['numpages'] = comments[-1]['page'] + 1
    return render_template('blog/one_post.html', posts=posts, pager=pager,
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
    if len(body) > MAX_POST_LEN:
        return 'Пост слишком длинный. Попробуйте разбить его на несколько частей'
    return None

def do_create_post(title, body, anon, paranoid):
    rendered = make_html(body)
    cut = autocut(body, AUTOCUT_POST_HEIGHT, False)
    if cut and cut != body:
        cut_rendered = make_html(cut)
    else:
        cut_rendered = ""
    author_id = g.user['id']
    if paranoid:
        author_id = 1 # anonymous
        anon = True

    db = get_db()
    db.execute(
        'INSERT INTO post (title, body, rendered, cut_rendered, author_id, anon)'
        ' VALUES (?, ?, ?, ?, ?, ?)',
        (title, body, rendered, cut_rendered, author_id, anon)
    )
    db.commit()
    # add tags and upvote just created post
    post = db.execute('SELECT id FROM post WHERE author_id = ? ORDER BY id DESC LIMIT 1', (author_id,)).fetchone()
    if post:
        add_tags(body, post['id'], remove_old_tags=False)
        if not paranoid:
            add_vote(author_id, g.user['is_golden'], post['id'], 2)
            return redirect(url_for('blog.one_post', id=post['id'])), post['id']
        else:
            add_vote(1, False, post['id'], 1)
            return redirect(url_for('blog.new')), post['id']
    else:
        return redirect(url_for('blog.index')), None


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
            res, _ = do_create_post(title, body, anon, paranoid)
            return res

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
                (title, body, rendered, datetime.now(), is_moderator_edit(post), id)
            )
            db.commit()
            add_tags(body, post['id'], remove_old_tags=True)
            return redirect(url_for('blog.one_post', id=id))

    return render_template('blog/update.html', post=post)

def get_comment_to_update(id):
    comment = get_db().execute(
        'SELECT c.id, body, c.created, author_id, username, edited_by_moderator'
        ' FROM comment c JOIN user u ON c.author_id = u.id'
        ' WHERE c.id = ?',
        (id,)
    ).fetchone()

    if comment is None:
        abort(404, f"Comment id {id} doesn't exist.")

    if comment['edited_by_moderator'] and not g.user['is_moderator']:
        abort(403)

    if comment['author_id'] != g.user['id'] and not g.user['is_moderator']:
        abort(403)

    return comment

@bp.route('/<int:post_id>/updatecomment/<int:comment_id>', methods=('GET', 'POST'))
@login_required
def updatecomment(post_id, comment_id):
    comment = get_comment_to_update(comment_id)

    if request.method == 'POST':
        body = request.form['body']

        if len(body) > MAX_COMMENT_LEN:
            flash('Вы попытались оставить слишком длинный комментарий')
        else:
            update_or_delete_user_comment(is_moderator_edit(comment), body, post_id, comment_id)

        return redirect(url_for('blog.one_post', id=post_id) + "#answer" + str(comment_id))

    return render_template('blog/updatecomment.html', comment=comment)

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

def check_comment(post_id, text, as_separate_post):
    if not post_id:
        return 'Что-то сломалось или вы делаете что-то странное'
    if not text:
        return 'Нужно что-нибудь написать'
    if as_separate_post:
        max_len = MAX_POST_LEN
    else:
        max_len = MAX_COMMENT_LEN
    if len(text) > max_len:
        return 'Вы пытаетесь оставить слишком длинный комментарий'
    return None

def do_create_comment(text, post_id, parent_id, anon, paranoid, linked_post_id):
    rendered = make_html(text, do_embeds=False)
    author_id = g.user['id']
    if paranoid:
        author_id = 1 # anonymous
        anon = True
    add_comment(text, rendered, author_id, post_id, parent_id, anon, linked_post_id)
    if parent_id:
        anchor = "#answer" + str(parent_id)
    else:
        anchor = "#answersection"

    # upvote just created comment
    if not paranoid:
        comment = get_db().execute('SELECT id FROM comment WHERE author_id = ? ORDER BY id DESC LIMIT 1', (author_id,)).fetchone()
        if comment:
            add_comment_vote(author_id, g.user['is_golden'], post_id, comment['id'], 2)
            anchor = "#answer" + str(comment['id'])
    return redirect(url_for('blog.one_post', id=post_id) + anchor)

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
    as_separate_post = 'newpost' in request.form and request.form['newpost'] == 'on'

    error = check_user_permissions_to_comment(get_db())
    if not error:
        error = check_comment(post_id, text, as_separate_post)

    if error is not None:
        flash(error)
        return redirect(url_for('blog.one_post', id=post_id))
    else:
        if as_separate_post:
            parent_post = get_posts_by_id(post_id)
            if len(parent_post) > 0:
                title = parent_post[0]['title']
                if 'Ответ на запись ' not in title:
                    title = f'Ответ на запись "{title}"'
            else:
                title = "Ответ"
            _, answer_id = do_create_post(title, f'> [{title}](/{post_id})\n\n' + text, anon, paranoid)
            cut_text = autocut(text, AUTOCUT_COMMENT_HEIGHT, True)
            if (cut_text == text) or (answer_id is None):
                return do_create_comment(text, post_id, parent_id, anon, paranoid, answer_id)
            else:
                answer_text = f'{cut_text}\n[Читать дальше →](/{answer_id})'
                return do_create_comment(answer_text, post_id, parent_id, anon, paranoid, answer_id)
        else:
            return do_create_comment(text, post_id, parent_id, anon, paranoid, None)
