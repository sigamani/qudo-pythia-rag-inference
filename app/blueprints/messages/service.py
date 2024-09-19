import logging
import time

from flask import abort, current_app, g
from mongoengine import Q

from app.utils.cache_utils.message_cache_service import MessageCacheService
from app.utils.chatbot.chatbot_utils import create_gpt_prompt
from app.utils.chatbot.gpt_utils.chatgpt_bot import Chatbot
from app.utils.chatbot.langchain_bot import PythiaChatbot
from app.utils.chatbot.langchain_utils.data_handler import PythiaDataHandler
from app.utils.feedback_model import Feedback

from ...utils.chatbot.langchain_utils.mongo_utils import MongoDBHandler
from ...utils.chatbot.langchain_utils.question_generator import PythiaQuestionGenerator
from .models.message import Message
from .serializer import serialize, serialize_gpt_prompt

logger = logging.getLogger("qudo")


# Specific function just to filter messages based on filters passed
def fetch_messages(filters, order_by=None):
    query = Q(**filters)
    query = query & Q(user_id=g.user["id"])
    messages = Message.objects(query)
    if messages:
        if order_by:
            messages = messages.order_by(order_by)
        return messages
    return None


def fetch_message_count(filters):
    query = Q(**filters)
    return Message.objects(query).count()


def process_create_message(payload):
    """
    Processes the creation of a new message for a conversation.

    Args:
        payload (dict): The payload containing the conversation ID and question.

    Returns:
        Message: The created message.
    """
    conversation_id = payload["conversation_id"]

    data = MessageCacheService().get_data(conversation_id)

    segmentation = data["segmentation"]
    segment = data["segment"]
    segment_id = data["segment_id"]
    survey_id = data["survey_id"]
    seg_description = data["seg_description"]

    question = payload["question"]

    chatbot = Chatbot(
        openai_key=current_app.config["OPENAI_API_KEY"],
        question=question,
        survey_id=survey_id,
        segmentation=segmentation,
        segment_id=segment_id,
        segment_description=seg_description,
        messages=[],
    )
    # logger.info(data["messages"])
    if not data["messages"]:
        messages = chatbot.generate_base_message([], [])
        logger.info(f"Messages: {messages}")

        for item in messages:
            message = Message(**item)
            message.user_id = g.user["id"]
            message.conversation_id = conversation_id
            message.is_visible = False
            message.is_bot = True
            message.save()

            data["messages"].append(serialize_gpt_prompt(message))

    question_message = Message(
        user_id=g.user["id"], conversation_id=conversation_id, content=question, role="user", is_bot=False
    )
    question_message.save()

    start_time = time.time()

    chatbot.set_messages(data["messages"])
    gpt_prompt = create_gpt_prompt(question, data["survey"], segment, chatbot)

    # Calculate the elapsed time
    elapsed_time = time.time() - start_time

    logger.info(f"Execution time: {elapsed_time} seconds")

    message = Message(
        user_id=g.user["id"], conversation_id=conversation_id, content=gpt_prompt, role="assistant", is_bot=True
    )
    message.save()

    data["messages"].append(serialize_gpt_prompt(question_message))
    data["messages"].append(serialize_gpt_prompt(message))

    logger.info(f'redis messages: {data["messages"]}')

    MessageCacheService().set_data(conversation_id, data)
    response = {
        "question": serialize(question_message),
        "message": serialize(message),
    }

    return response


def create_message(conversation_id, content, role, is_bot, is_visible=True):
    message = Message(
        user_id=g.user["id"],
        conversation_id=str(conversation_id),
        content=content,
        role=role,
        is_bot=is_bot,
        is_visible=is_visible,
    )
    message.save(validate=False)
    message.reload()
    return message


def process_add_feedback(message_id, payload):
    query = fetch_messages({"id": message_id})
    if not query:
        abort(400, description="Message Not Found")
    message = query.get()
    feedback = message.feedback or Feedback()
    feedback.reaction = payload.get("reaction", None)
    feedback.comment = payload.get("comment", None)
    message.feedback = feedback
    message.save(validate=False)
    message.reload()
    return message


def process_create_message_langchain(payload):
    """
    Processes the creation of a new message for a conversation.

    Args:
        payload (dict): The payload containing the conversation ID and question.

    Returns:
        Message: The created message.
    """
    conversation_id = payload["conversation_id"]

    data = _initialize_cache_data(conversation_id)

    data_handler, mongo_handler = _initialize_data_handlers(current_app.config, data)
    question, question_message = _create_question_message(conversation_id, payload)
    chat_history = data["history"]

    question_generator = PythiaQuestionGenerator(data_handler, current_app.config["OPENAI_API_KEY"])

    answer = _generate_chatbot_response(question_generator, mongo_handler, question, chat_history)
    answer_message = _create_answer_message(conversation_id, answer)

    _update_chat_history(conversation_id, data, question, answer)
    response = {
        "question": serialize(question_message),
        "message": serialize(answer_message),
    }

    return response


def _initialize_cache_data(conversation_id):
    data = MessageCacheService().get_data(conversation_id)
    return data


def _initialize_data_handlers(config, data):
    """
    Initializes the data handlers for a given conversation.

    Args:
        config (dict): The configuration settings, typically from Flask's current_app.config.
        data (dict): The conversation data friom cache.

    Returns:
        tuple: A tuple containing initialized instances of PythiaDataHandler, MongoDBHandler, and conversation data.
    """
    # data = MessageCacheService().get_data(conversation_id)

    segmentation = data["segmentation"]
    segment = data["segment"].replace(segmentation + "_", "")
    survey_name = data["survey"]

    data_handler = PythiaDataHandler(survey_name, segmentation, segment, config["S3_DS_ENVIRONMENT"])
    survey_name = survey_name + f"_{ config['S3_DS_ENVIRONMENT']}"
    mongo_handler = MongoDBHandler(
        survey_name,
        segmentation,
        segment,
        config["MONGODB_ATLAS_CLUSTER_URI"],
        config["OPENAI_API_KEY"],
        config["MONGO_DB_URL"],
        config["MONGO_PUBLIC_KEY"],
        config["MONGO_PRIVATE_KEY"],
        config["MONGO_CLUSTER"],
        config["MONGO_GROUP_ID"],
        data_handler,
    )
    return data_handler, mongo_handler


def _create_question_message(conversation_id, payload):
    """
    Creates and saves a message object for the user's question in the conversation.

    Args:
        conversation_id (str): The unique identifier of the conversation.
        payload (dict): The payload containing the user's question.

    Returns:
        str: The user's question extracted from the payload.
    """
    question = payload["question"]
    question_message = Message(
        user_id=g.user["id"], conversation_id=conversation_id, content=question, role="user", is_bot=False
    )
    question_message.save()
    return question, question_message


def _generate_chatbot_response(question_generator, mongo_handler, question, chat_history):
    """
    Generates a response to the user's question using the chatbot.

    Args:
        question_generator (PythiaQuestionGenerator): The question generator instance.
        mongo_handler (MongoDBHandler): The MongoDB handler instance.
        question (str): The user's question.
        chat_history (list): The chat history of the conversation.

    Returns:
        str: The chatbot's response to the question.
    """
    chatbot = PythiaChatbot(
        "gpt-4",
        openai_key=current_app.config["OPENAI_API_KEY"],
        mongo_handler=mongo_handler,
        question_generator=question_generator,
    )
    response = chatbot.generate_chatbot()({"question": question, "chat_history": chat_history})
    return response["answer"]


def _create_answer_message(conversation_id, answer):
    """
    Creates and saves a message object for the chatbot's answer in the conversation.

    Args:
        conversation_id (str): The unique identifier of the conversation.
        answer (str): The chatbot's answer to the user's question.

    Returns:
        Message: The created Message object for the chatbot's answer.
    """
    message = Message(
        user_id=g.user["id"], conversation_id=conversation_id, content=answer, role="assistant", is_bot=True
    )
    message.save()
    return message


def _update_chat_history(conversation_id, data, question, answer):
    """
    Updates the chat history in the cache with the new question-answer pair.

    Args:
        conversation_id (str): The unique identifier of the conversation.
        data (dict): The current conversation data.
        question (str): The user's question.
        answer (str): The chatbot's answer.

    Returns:
        None
    """
    new_chat_history = (question, answer)
    data["history"].append(new_chat_history)
    MessageCacheService().set_data(conversation_id, data)
