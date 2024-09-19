from datetime import datetime

from mongoengine import DateTimeField, EmbeddedDocument, IntField, StringField


class Feedback(EmbeddedDocument):
    rating = IntField(required=False, default=0)
    comment = StringField(required=False, default="")
    reaction = StringField(required=False, choices=["thumbs_up", "thumbs_down"])
    created_at = DateTimeField(required=True, default=datetime.utcnow)
    modified_at = DateTimeField(default=datetime.utcnow)

    meta = {"strict": False}
