import logging
import math

from flask import Blueprint, abort, current_app, g, jsonify, request
from mongoengine.errors import DoesNotExist

from app.utils.mapping_utils import Mapping
from app.utils.request_response_utils import make_json_response

from .models.conversation import Conversation
from .serializer import deserialize, serialize, serialize_list
from .service import (
    fetch_conversations,
    process_add_feedback,
    process_create,
    process_update,
)

logger = logging.getLogger("qudo")


conversation_bp = Blueprint("conversation_api", __name__)


@conversation_bp.route("", methods=["GET"])
def index():
    page_number = int(request.args.get("page", default=1))
    per_page = int(request.args.get("per_page", current_app.config.get("PER_PAGE")))
    max_per_page = current_app.config.get("MAX_PER_PAGE")
    per_page = per_page if per_page <= max_per_page else max_per_page
    offset = (page_number - 1) * per_page
    query = fetch_conversations({}, request.args.get("order_by", "-modified_at"))
    conversations = query.skip(offset).limit(per_page)
    total_count = query.count()
    return make_json_response(
        serialize_list(conversations),
        200,
        {
            "per_page": per_page,
            "page": page_number,
            "total_pages": math.ceil(total_count / per_page) if per_page > 0 else 0,
            "total_count": total_count,
        },
    )


@conversation_bp.route("", methods=["POST"])
def create_conversation():
    if not request.is_json:
        abort(400, description="Missing json in the request")
    payload = request.get_json()
    if not any(key in ["survey", "segmentation"] for key in payload):
        abort(400, description="Missing required parameters")
    conversation, message = process_create(deserialize(payload), payload)
    response = {"conversation": serialize(conversation), "message": message}
    return make_json_response(data=response, status_code=201)


@conversation_bp.route("/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    query = fetch_conversations({"id": conversation_id}, request.args.get("order_by", "-modified_at"))
    if not query:
        abort(400, description="Not Found")
    conversation = query.get()
    return make_json_response(serialize(conversation), 200)


@conversation_bp.route("/<conversation_id>", methods=["PATCH"])
def update_conversation(conversation_id):
    if not request.is_json:
        abort(400, description="Missing json in the request")
    payload = request.get_json()
    conversation = process_update(payload, conversation_id)
    return make_json_response(serialize(conversation), 200)


# Update a conversation by ID
@conversation_bp.route("/<conversation_id>/feedback", methods=["PUT"])
def conversation_feedback(conversation_id):
    if not request.is_json:
        abort(400, description="Missing json in the request")
    payload = request.get_json()
    conversation = process_add_feedback(conversation_id, payload)
    return make_json_response(serialize(conversation), 200)


# Delete a conversation by ID
@conversation_bp.route("/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        conversation.delete()
        return jsonify({"message": "Conversation deleted"}), 204
    except DoesNotExist:
        return jsonify({"error": "Conversation not found"}), 404


@conversation_bp.route("/prompts", methods=["GET"])
def get_prompts():
    segmentation_name = request.args.get("segmentation")
    return make_json_response(Mapping.INITIAL_PROMPTS[segmentation_name], 200)
