from app import db, settings
from datetime import datetime


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    create_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow(), index=True)
    deleted = db.Column(db.Boolean)

    username = db.Column(db.String())
    password = db.Column(db.String())
    last_action = db.Column(db.DateTime())
    fail_count = db.Column(db.Integer())
    active = db.Column(db.Boolean())

    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    service = db.relationship('Service', backref=db.backref('accounts', lazy='dynamic'))

    def __init__(self):
        self.fail_count = 0

    def generate_username(self):
        import random
        name = random.choice(settings.NAMES)
        name += str(random.randint(0, 255))
        self.username = name
        return self.username

    def generate_password(self):
        import random
        self.password = ""
        for i in xrange(0, 12):
            self.password += str(random.randint(0, 9))

        return self.password

    def fill(self, service):
        self.active = False
        self.service = service
        self.generate_username()
        self.generate_password()
        db.session.add(self)
        db.session.commit()
        return self.username, self.password
