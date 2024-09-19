import logging

from flask import Blueprint, abort, request

from app.utils.request_response_utils import make_json_response

from .serializer import serialize, serialize_list
from .service import fetch_messages, process_add_feedback, process_create_message

logger = logging.getLogger("qudo")

message_bp = Blueprint("message_api", __name__)


@message_bp.route("", methods=["POST"])
def create_message():
    if not request.is_json:
        abort(400, description="Missing json in the request")
    payload = request.get_json()
    response = process_create_message(payload)
    return make_json_response(response, 200)


@message_bp.route("/<conversation_id>", methods=["GET"])
def get_messages(conversation_id):
    query = fetch_messages({"conversation_id": conversation_id})
    if not query:
        abort(400, description="Not Found")
    messages = query.all()
    return make_json_response(serialize_list(messages), 200)


@message_bp.route("/<message_id>/feedback", methods=["PUT"])
def message_feedback(message_id):
    if not request.is_json:
        abort(400, description="Missing json in the request")
    payload = request.get_json()
    conversation = process_add_feedback(message_id, payload)
    return make_json_response(serialize(conversation), 200)
