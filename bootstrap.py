from models.service import Service
from models.account import Account
from app import db, settings

_pyflakes = Account

db.drop_all()
db.create_all()

s = Service()
s.type = "reddit"

opt = {
    'host': 'http://%s:%s/captcha' % (settings.CAPTCHA_HOST, settings.CAPTCHA_PORT),
    'headless': False
}

s.set_options(opt)

db.session.add(s)
db.session.commit()
