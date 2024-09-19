from datetime import datetime

from mongoengine import DateTimeField, Document, EmbeddedDocumentListField, StringField

from app.utils.base_models import BaseQuerySet, CustomDocument

from .message import Message


class Trial(Document, CustomDocument):
    trial_id = StringField()
    messages = EmbeddedDocumentListField(Message)
    survey = StringField()
    survey_id = StringField()
    segment = StringField()
    segment_id = StringField()
    segmentation = StringField()
    description = StringField()
    created_at = DateTimeField(required=True, default=datetime.utcnow)
    modified_at = DateTimeField(default=datetime.utcnow)

    meta = {"strict": False, "queryset_class": BaseQuerySet, "indexes": ["trial_id"]}
