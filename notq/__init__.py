import os
from flask import Flask

def create_app(test_config=None):
    global app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE='sqlite+pysqlite:///' + os.path.join(app.instance_path, 'notq.sqlite')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import robopost
    app.cli.add_command(robopost.robopost_command)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import feed
    app.register_blueprint(feed.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')
    
    return app
