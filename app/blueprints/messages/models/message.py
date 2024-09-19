from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    EmbeddedDocumentField,
    StringField,
)

from app.utils.base_models import BaseQuerySet, CustomDocument
from app.utils.feedback_model import Feedback


class Message(Document, CustomDocument):
    """
    Represents a message within a conversation.

        Attributes:
            user_id (str): The user's unique identifier who sent the message.

            conversation_id (str): The unique identifier of the conversation to which the message belongs.

            content (str): The content of the message.

            feedback (Feedback): An embedded document representing feedback related to the message.

            created_at (datetime): The timestamp when the message was created (default is the current UTC time).

            modified_at (datetime): The timestamp when the message was last modified (default is the current UTC time).

        Meta:
            strict (bool): Indicates if the document should follow strict field validation (False).
            queryset_class (BaseQuerySet): The custom query set class to use.
            indexes (list of str): A list of fields on which indexes should be created for efficient querying.

    """

    user_id = StringField(required=True)
    conversation_id = StringField(required=True)
    content = StringField(required=True)
    role = StringField(choices=["user", "system", "assistant", "initial"])
    is_visible = BooleanField(default=True)
    is_bot = BooleanField(required=True, default=False)
    feedback = EmbeddedDocumentField(Feedback)
    created_at = DateTimeField(required=True, default=datetime.utcnow)
    modified_at = DateTimeField(default=datetime.utcnow)
    meta = {"strict": False, "queryset_class": BaseQuerySet, "indexes": ["user_id", "conversation_id"]}
