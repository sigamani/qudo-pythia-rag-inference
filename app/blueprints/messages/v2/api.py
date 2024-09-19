import logging

from flask import Blueprint, abort, request

from app.utils.request_response_utils import make_json_response

from ..serializer import serialize
from ..service import process_create_message_langchain

logger = logging.getLogger("qudo")

message_v2_bp = Blueprint("message_v2_api", __name__)


@message_v2_bp.route("", methods=["POST"])
def create_message():
    if not request.is_json:
        abort(400, description="Missing json in the request")
    payload = request.get_json()
    response = process_create_message_langchain(payload)
    return make_json_response(response, 200)
