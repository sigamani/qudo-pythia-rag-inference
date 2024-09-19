import logging

from flask import abort, g
from mongoengine import Q
from mongoengine.errors import DoesNotExist

from app.utils.feedback_model import Feedback

from .models.conversation import Conversation

logger = logging.getLogger("qudo")

UPDATABLE_FIELDS = ["title"]


def fetch_conversations(filters, order_by=None):
    query = Q(**filters)
    query = query & Q(user_id=g.user["id"])
    try:
        query = Conversation.objects(query)
    except DoesNotExist:
        raise DoesNotExist("Conversation not found")
    except Exception as e:
        logger.error(e)
        raise e
    if order_by:
        query = query.order_by(order_by)
    return query


def get_conversation_by_ids(conversation_ids):
    if not conversation_ids:
        return []
    return fetch_conversations({"id__in": conversation_ids}).only("id", "title", "survey", "segment")


def process_update(conversation_data, conversation_id):
    query = fetch_conversations({"id": conversation_id})
    if not query:
        abort(400, description="Not Found")

    conversation = query.first()
    for key in UPDATABLE_FIELDS:
        if conversation_data.get(key) is not None:
            conversation[key] = conversation_data[key]
    conversation.save(validate=False)
    conversation.reload()
    return conversation


def process_create(conversation, conversation_data):
    logger.info(f"create conversation: {conversation_data}")
    conversation.user_id = g.user["id"]
    conversation.save(validate=False)
    conversation.reload()
    message_content = (
        f'You\'re chatting with Sarah, an AI bot representing the {conversation_data["segment"].split("_")[-1]} segment'
    )

    from app.blueprints.messages.service import create_message
    from app.blueprints.messages.serializer import serialize as message_serializer

    message = create_message(conversation.id, message_content, "initial", True, True)
    return conversation, message_serializer(message)


def process_add_feedback(conversation_id, payload):
    query = fetch_conversations({"id": conversation_id})
    if not query:
        abort(400, description="Not Found")
    conversation = query.get()
    feedback = Feedback(**payload)
    conversation.feedback = feedback
    conversation.save(validate=False)
    conversation.reload()
    return conversation
