import asyncio
from datetime import datetime
from flask import current_app
from telegram import Bot
from telegram.helpers import escape_markdown

from notq.db_structure import select_posts_with_votes
from notq.db import db_execute_commit, get_db
from notq.db_structure import post_table

def send_post_to_tg_if_needed(id):
    if not 'TG_BOT_TOKEN' in current_app.config:
        return
    post = get_db().execute(select_posts_with_votes().where(post_table.c.id == id)).fetchone()
    if not post or post.sent_to_tg:
        return
    send_telegram_message(post)

# this is a super-rough and dump way to send telegram messages (because it's basically synchronous)
# but still better than nothing

def send_telegram_message(post):
    token = current_app.config['TG_BOT_TOKEN']
    if token and should_send_to_tg(post):
        channel = current_app.config['TG_CHANNEL_ID']
        msg = create_tg_message(post)
        asyncio.run(do_send_tg_message(token, channel, msg, post.id))

def should_send_to_tg(post):
    return post.weighted_votes >= current_app.config['TG_WEIGHTED_VOTES_THRESHOLD']

def create_tg_message(post):
    title = escape_markdown(post.title, version=2)
    linked_title = f'[{title}](https://notq.ru/{post.id})'
    if not post.anon:
        body = f"автор - {post.username}"
    else:
        body = 'автор пожелал остаться анонимным'
    return linked_title + '\n' + escape_markdown(body, version=2)

async def do_send_tg_message(token, channel, msg, id):
    bot = Bot(token)
    print('Finally sending message:\n', msg)
    print(' to ', channel)
    send_message = bot.sendMessage(chat_id=channel, text=msg, parse_mode='MarkdownV2')
    db_execute_commit('UPDATE post SET sent_to_tg=:t WHERE id=:p', t=datetime.now(), p=id)
    await send_message
