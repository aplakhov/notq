from sqlalchemy import Boolean, ForeignKey, MetaData, Table, Column, Integer, Float, String, DateTime, UniqueConstraint, func, Index, select

db_metadata = MetaData()

user_table = Table('notquser', db_metadata, 
                   Column('id', Integer, primary_key=True),
                   Column('username', String, unique=True, nullable=False),
                   Column('password', String, nullable=False),
                   Column('created', DateTime(), server_default=func.now()),
                   Column('about', String),
                   Column('is_golden', Boolean, default=False),
                   Column('is_moderator', Boolean, default=False),
                   Column('banned_until', DateTime()),
                   Column('about_post_id', Integer, ForeignKey('post.id', name='fk_notquser_about_post', ondelete='set null'))
                   )
Index("idx_user_name", user_table.c.username)

post_table = Table('post', db_metadata,
                   Column('id', Integer, primary_key=True),
                   Column('author_id', Integer, ForeignKey('notquser.id', name='fk_post_author'), nullable=False),
                   Column('created', DateTime(), server_default=func.now()),
                   Column('edited', DateTime()),
                   Column('title', String, nullable=False),
                   Column('body', String, nullable=False),
                   Column('rendered', String, nullable=False),
                   Column('cut_rendered', String),
                   Column('anon', Boolean),
                   Column('show_in_feed', Boolean, nullable=False, default=True),
                   Column('edited_by_moderator', Boolean),
                   Column('sent_to_tg', DateTime()),
                   Column('views', Integer, default=0)
                   )
Index("idx_post_created", post_table.c.created)
Index("idx_post_author", post_table.c.author_id)

vote_table = Table('vote', db_metadata,
                   Column('user_id', Integer, ForeignKey('notquser.id', ondelete='cascade'), nullable=False),
                   Column('post_id', Integer, ForeignKey('post.id', ondelete='cascade'), nullable=False),
                   Column('vote', Integer, nullable=False),
                   Column('weighted_vote', Integer, nullable=False),
                   Column('karma_vote', Float, nullable=False),
                   UniqueConstraint("user_id", "post_id")
                   )

comment_table = Table('comment', db_metadata,
                   Column('id', Integer, primary_key=True),
                   Column('author_id', Integer, ForeignKey('notquser.id'), nullable=False),
                   Column('created', DateTime(), server_default=func.now()),
                   Column('edited', DateTime()),
                   Column('body', String, nullable=False),
                   Column('rendered', String, nullable=False),
                   Column('post_id', Integer, ForeignKey('post.id', ondelete='cascade'), nullable=False),
                   Column('parent_id', Integer),
                   Column('anon', Boolean),
                   Column('edited_by_moderator', Boolean),
                   Column('linked_post_id', Integer, ForeignKey('post.id', ondelete='cascade')),
                )
Index("idx_comment_post", comment_table.c.post_id)
Index("idx_comment_author", post_table.c.author_id)

commentvote_table = Table('commentvote', db_metadata,
                        Column('user_id', Integer, ForeignKey('notquser.id', ondelete='cascade'), nullable=False),
                        Column('post_id', Integer, ForeignKey('post.id', ondelete='cascade'), nullable=False),
                        Column('comment_id', Integer, ForeignKey('comment.id', ondelete='cascade'), nullable=False),
                        Column('vote', Integer, nullable=False),
                        Column('weighted_vote', Integer, nullable=False),
                        Column('karma_vote', Float, nullable=False),
                        UniqueConstraint("user_id", "post_id", "comment_id")
                    )
Index("idx_commentvote_post", commentvote_table.c.post_id)

tag_table = Table('tag', db_metadata,
                Column('id', Integer, primary_key=True),
                Column('tagname', String, unique=True, nullable=False)
            )
Index('idx_tag_name', tag_table.c.tagname)

posttag_table = Table('posttag', db_metadata,
                    Column('tag_id', Integer, ForeignKey('tag.id'), nullable=False),
                    Column('post_id', Integer, ForeignKey('post.id', ondelete='cascade'), nullable=False),
                    UniqueConstraint("tag_id", "post_id")
                )
Index('idx_posttag_tag', posttag_table.c.tag_id)

notifies_table = Table('notifies', db_metadata,
                    Column('user_id', Integer, ForeignKey('notquser.id', ondelete='cascade'), nullable=False),
                    Column('post_id', Integer, ForeignKey('post.id', ondelete='cascade')),
                    Column('text', String, nullable=False),
                    Column('created', DateTime(), server_default=func.now()),
                    Column('is_read', Boolean, default=False),
                )
idx_notify_user_post = Index('idx_notify_user_post', notifies_table.c.user_id, notifies_table.c.post_id)

def select_posts_with_votes():
    query = select(
        post_table.c.id,
        post_table.c.title,
        post_table.c.body,
        post_table.c.rendered,
        post_table.c.cut_rendered,
        post_table.c.created,
        post_table.c.anon,
        post_table.c.edited,
        post_table.c.edited_by_moderator,
        post_table.c.author_id,
        post_table.c.sent_to_tg,
        post_table.c.views,
        user_table.c.username,
        user_table.c.is_golden,
        func.sum(vote_table.c.vote).label('votes'),
        func.sum(vote_table.c.weighted_vote).label('weighted_votes'),
    )
    query = query.join(user_table, user_table.c.id==post_table.c.author_id)
    query = query.join(vote_table, vote_table.c.post_id==post_table.c.id)
    query = query.group_by(post_table.c.id, user_table.c.id)
    return query

def select_comments_with_votes():
    query = select(
        comment_table.c.id,
        comment_table.c.author_id,
        comment_table.c.post_id,
        comment_table.c.created,
        comment_table.c.body,
        comment_table.c.rendered,
        comment_table.c.parent_id,
        comment_table.c.anon,
        comment_table.c.edited,
        comment_table.c.edited_by_moderator,
        user_table.c.username,
        user_table.c.is_golden,
        func.sum(commentvote_table.c.vote).label('votes'),
        func.sum(commentvote_table.c.weighted_vote).label('weighted_votes'),
        post_table.c.title
    )
    query = query.join(user_table, user_table.c.id==comment_table.c.author_id)
    query = query.join(post_table, post_table.c.id==comment_table.c.post_id)
    query = query.join(commentvote_table, commentvote_table.c.comment_id==comment_table.c.id)
    query = query.group_by(comment_table.c.id, post_table.c.id, user_table.c.id)
    return query
