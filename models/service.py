from app import db
from datetime import datetime
import json


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    create_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow(), index=True)
    deleted = db.Column(db.Boolean)

    type = db.Column(db.String())
    options_s = db.Column(db.String())

    @property
    def options(self):
        import copy
        return json.loads(copy.copy(self.options_s))

    def set_options(self, option):
        self.options_s = json.dumps(option)
