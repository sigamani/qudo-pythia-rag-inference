from flask import g
from .models.message import Message
from app.utils.permission_utils import filter_allowed_data
from app.blueprints.conversations.service import get_conversation_by_ids


def deserialize(data, message_id=None):
    data = filter_allowed_data(data, g.permissions.get("Message", {}), 1)
    message = Message.from_json(data)
    message.id = message_id
    return message


def serialize(message):
    message_json = message.to_clean_json_dict(follow_reference=True)
    return message_json


def serialize_list(messages):
    if not messages:
        return []
    conversation_ids = [message.conversation_id for message in messages]
    conversations = get_conversation_by_ids(conversation_ids)
    # Added check if permissions variable in 'g'
    if hasattr(g, "permissions"):
        id_conversation_mapping = {
            str(conversation.id): conversation.to_clean_json_dict(permissions=g.permissions)
            for conversation in conversations
        }
        messages_dict = messages.to_clean_json_dict(follow_reference=False, permissions=g.permissions)
    else:
        id_conversation_mapping = {
            str(conversation.id): conversation.to_clean_json_dict() for conversation in conversations
        }
        messages_dict = messages.to_clean_json_dict(follow_reference=False)
    for message_dict in messages_dict:
        conversation = id_conversation_mapping.get(message_dict["conversation_id"], message_dict["conversation_id"])
        message_dict["conversation"] = conversation

    return messages_dict


def serialize_gpt_prompt_list(messages):
    if not messages:
        return []
    message_history = []
    for message in messages:
        message_history.append(serialize_gpt_prompt(message))
    return message_history


def serialize_langchain_prompt_list(messages):
    if not messages:
        return []
    qa_pairs = []
    question = None

    for message in messages:
        if not message.is_bot:
            # If current message is from the user, store it as a question
            question = message.content
        elif question is not None:
            # If current message is from the bot and there is a stored question
            answer = message.content
            qa_pairs.append((question, answer))
            # Reset question for the next pair
            question = None

    return qa_pairs


def serialize_gpt_prompt(message):
    if not message:
        return None
    return {"role": message.role, "content": message.content}
