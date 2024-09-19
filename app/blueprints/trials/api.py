import logging
import math

from flask import Blueprint, abort, request

from app.utils.request_response_utils import make_json_response

from .serializer import deserialize, serialize, serialize_trial_message
from .service import (
    process_add_llm_message,
    process_add_message,
    process_create_trial,
    process_get_trial,
)

logger = logging.getLogger("qudo")


trial_bp = Blueprint("trials_api", __name__)


@trial_bp.route("", methods=["POST"])
def create_trial():
    if not request.is_json:
        abort(400, description="Missing json in the request")
    payload = request.get_json()
    if not any(key in ["survey", "segmentation"] for key in payload):
        abort(400, description="Missing required parameters")
    trial, message = process_create_trial(deserialize(payload), payload)
    response = {"trial": serialize(trial), "message": serialize_trial_message(message)}
    return make_json_response(data=response, status_code=201)


@trial_bp.route("/<trial_id>", methods=["GET"])
def get_trial(trial_id):
    response = process_get_trial(trial_id)
    return make_json_response(response, 200)


@trial_bp.route("/<trial_id>", methods=["POST"])
def add_message(trial_id):
    # response = process_add_message(trial_id, request.get_json())
    response = process_add_llm_message(trial_id, request.get_json())
    return make_json_response(data=response, status_code=201)
