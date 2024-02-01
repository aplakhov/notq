import os
import tempfile

import pytest
from notq import create_app
from notq.auth import do_load_user
from notq.data_model import get_best_posts, get_top_posts
from notq.db import init_db
from notq.karma import get_user_karma

@pytest.fixture
def app():
    use_sqlite = False
    if use_sqlite:
        db_fd, db_path = tempfile.mkstemp()
        app = create_app({
            'TESTING': True,
            'DATABASE': 'sqlite+pysqlite:///' + db_path,
        })
    else:
        app = create_app({})
        app.config.from_pyfile('config_testing.py', silent=True)

    with app.app_context():
        init_db()

    #there definitely should exist a better way
    do_load_user.cache_clear()
    get_user_karma.cache_clear()
    get_top_posts.cache_clear()
    get_best_posts.cache_clear()

    yield app

    if use_sqlite:
        os.close(db_fd)
        os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()
