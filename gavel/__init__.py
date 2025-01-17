# Copyright (c) Anish Athalye (me@anishathalye.com)
#
# This software is released under AGPLv3. See the included LICENSE.txt for
# details.

from flask import Flask
app = Flask(__name__)

import gavel.settings as settings
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['SERVER_NAME'] = settings.SERVER_NAME

if settings.PROXY:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

from flask_assets import Environment, Bundle
assets = Environment(app)
assets.config['pyscss_style'] = 'expanded'
scss = Bundle(
    'css/style.scss',
    depends='**/*.scss',
    filters=('libsass',),
    output='all.css'
)
assets.register('scss_all', scss)

from celery import Celery
import ssl

# Modify the Redis URL to include SSL parameters
redis_url = settings.BROKER_URI
if redis_url.startswith('rediss://'):
    redis_url = f"{redis_url}?ssl_cert_reqs=CERT_NONE"

app.config['CELERY_BROKER_URL'] = redis_url
app.config['CELERY_RESULT_BACKEND'] = redis_url

celery = Celery(
    app.name,
    broker=redis_url,
    backend=redis_url
)

# Configure Celery
celery.conf.update({
    'broker_connection_retry_on_startup': True,
    'broker_connection_max_retries': 10,
    'redis_backend_use_ssl': {
        'ssl_cert_reqs': ssl.CERT_NONE
    },
    'broker_use_ssl': {
        'ssl_cert_reqs': ssl.CERT_NONE
    }
})

# Create base task class with Flask app context
class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask

from gavel.models import db
db.app = app
db.init_app(app)

import gavel.template_filters # registers template filters

import gavel.controllers # registers controllers
