from mongoengine import BooleanField, EmbeddedDocument, StringField


class Message(EmbeddedDocument):
    content = StringField(required=True)
    role = StringField(choices=["user", "system", "assistant", "initial"])
    is_visible = BooleanField(default=True)
    is_bot = BooleanField(required=True, default=False)

    meta = {"strict": False}
