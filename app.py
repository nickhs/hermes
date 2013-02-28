from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
import settings
import redis
_pyflakes = settings

app = Flask(__name__)
app.config.from_pyfile('settings.py')

db = SQLAlchemy(app)

celery = Celery(app)
celery.add_defaults(app.config)

redis = redis.StrictRedis(host=settings.REDIS_URL,
            port=settings.REDIS_PORT, db=settings.REDIS_DB)
