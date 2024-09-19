import json

from flask import g

from app.blueprints.messages.serializer import serialize_list as serialize_message_list
from app.blueprints.messages.service import fetch_message_count, fetch_messages
from app.utils.permission_utils import filter_allowed_data

from ...utils.cache_utils.user_cache_service import get_user
from .models.conversation import Conversation


def add_user_details(conversation, user_id):
    # Add user details in conversation
    try:
        user_details = get_user(user_id)
        conversation["user__name"] = user_details.get("name")
        conversation["user__email"] = user_details.get("email")
    except:
        pass
    return conversation


def deserialize(data, conversation_id=None):
    data = filter_allowed_data(data, g.permissions.get("Conversation", {}), 1)
    if "qudo" not in data["segmentation"]:
        data["segmentation"] = f'qudo_{data["segmentation"]}'
    data["segmentation"] = data["segmentation"].lower().replace(" ", "_")
    data["segment"] = f'{data["segmentation"]}_{data["segment"]}'
    conversation = Conversation.from_json(json.dumps(data))
    conversation.id = conversation_id
    return conversation


def serialize(conversation):
    conversation_json = conversation.to_clean_json_dict(follow_reference=False)
    messages = fetch_messages({"conversation_id": str(conversation_json["_id"]), "is_visible": True}, "-modified_at")
    conversation_json["messages"] = serialize_message_list(messages)
    add_user_details(conversation_json, conversation_json["user_id"])
    return conversation_json


def serialize_list(conversations):
    conversation_list = conversations.to_clean_json_dict(follow_reference=False, permissions=g.permissions)
    for conversation in conversation_list:
        add_user_details(conversation, conversation["user_id"])
        conversation["message_count"] = fetch_message_count(
            {"conversation_id": str(conversation["_id"]), "is_visible": True}
        )
    return conversation_list


def serialize_admin(conversation):
    conversation_json = conversation.to_clean_json_dict(follow_reference=False)
    add_user_details(conversation_json, conversation_json["user_id"])
    return conversation_json
