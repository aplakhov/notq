import os
import tempfile

import pytest
from notq import create_app
from notq.db import init_db

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

    yield app

    if use_sqlite:
        os.close(db_fd)
        os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()
