import logging

from flask import Blueprint, abort
from mongoengine import Q

from app.blueprints.conversations.models.conversation import Conversation
from app.blueprints.conversations.serializer import serialize_admin, serialize_list
from app.blueprints.messages.models.message import Message
from app.blueprints.messages.serializer import serialize_list as serialize_message_list
from app.middlewares.auth.authorization import authorized
from app.utils.request_response_utils import make_json_response

logger = logging.getLogger("qudo")


admin_bp = Blueprint("admin_api", __name__)


@admin_bp.route("/conversation", methods=["GET"])
@authorized(roles=["INTERNAL_ADMIN", "SUPER_ADMIN"])
def index_conversations():
    query = Q()
    conversations = Conversation.objects(query).order_by("-created_at")
    return make_json_response(serialize_list(conversations), 200)


@admin_bp.route("/conversation/<conversation_id>", methods=["GET"])
@authorized(roles=["INTERNAL_ADMIN", "SUPER_ADMIN"])
def get_conversation(conversation_id):
    filters = {"id": str(conversation_id)}
    query = Q(**filters)
    conversation = Conversation.objects(query)

    if not conversation:
        abort(400, description="Not Found")
    return make_json_response(serialize_admin(conversation.get()), 200)


@admin_bp.route("/messages/<conversation_id>", methods=["GET"])
@authorized(roles=["INTERNAL_ADMIN", "SUPER_ADMIN"])
def get_messages(conversation_id):
    filters = {"conversation_id": str(conversation_id), "is_visible": True}
    query = Q(**filters)
    messages = Message.objects(query)

    if not messages:
        abort(400, description="Not Found")
    return make_json_response(serialize_message_list(messages), 200)
