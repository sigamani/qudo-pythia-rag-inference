from mongoengine import Document, StringField, DateTimeField, EmbeddedDocumentField, ListField
from app.utils.base_models import CustomDocument
from datetime import datetime
from app.utils.base_models import BaseQuerySet
from app.utils.feedback_model import Feedback


class Conversation(Document, CustomDocument):
    """
    Represents a conversation document.

        Attributes:
            user_id (str): The ID of the user associated with the conversation.

            feedback (EmbeddedDocumentField): The embedded document field for storing feedback.

            created_at (DateTimeField): The date and time when the conversation was created.

            modified_at (DateTimeField): The date and time when the conversation was last modified.

        Meta:
            strict (bool): Determines whether extra fields not defined in the model are allowed.

            queryset_class (BaseQuerySet): The custom query set class to use for querying documents.

            indexes (list): List of indexes to be created for efficient querying.

    """
    user_id = StringField(required=True)
    title = StringField()
    messages = ListField(StringField())
    survey = StringField()
    survey_id = StringField()
    segment = StringField()
    segment_id = StringField()
    segmentation = StringField()
    feedback = EmbeddedDocumentField(Feedback)
    created_at = DateTimeField(required=True, default=datetime.utcnow)
    modified_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "strict": False,
        'queryset_class': BaseQuerySet,
        'indexes': [
            'user_id'
        ]
    }
