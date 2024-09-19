import logging
import uuid

from flask import abort, current_app

from app.blueprints.messages.service import (
    _generate_chatbot_response,
    _initialize_data_handlers,
)

from ...utils.chatbot.chatbot_utils import create_gpt_prompt
from ...utils.chatbot.gpt_utils.chatgpt_bot import Chatbot
from ...utils.chatbot.gpt_utils.information_retrieval import get_description
from ...utils.chatbot.langchain_utils import PythiaQuestionGenerator
from ..messages.serializer import serialize_gpt_prompt, serialize_langchain_prompt_list
from .models.message import Message
from .models.trial import Trial
from .serializer import serialize, serialize_trial_message

logger = logging.getLogger("qudo")


def process_get_trial(trial_id):
    # Fetch the trial by its ID
    trial = Trial.objects(trial_id=trial_id).first()

    if not trial:
        abort(400, description="Trial not found")
    # Filter out messages where is_visible is False
    visible_messages = [message for message in trial.messages if message.is_visible]
    message_list = []
    for message in visible_messages:
        message_list.append(serialize_trial_message(message))
    trial_dict = serialize(trial)
    trial_dict.pop("messages")
    trial_dict["messages"] = message_list
    return trial_dict


def process_create_trial(trial, payload):
    logger.info(f"create trial: {payload}")
    trial_id = uuid.uuid4()
    trial.trial_id = str(trial_id)
    trial.save(validate=False)
    trial.reload()
    message_content = (
        f'You\'re chatting with Sarah, an AI bot representing the {payload["segment"].split("_")[-1]} segment'
    )
    message = create_trial_message(message_content, "initial", True, True)
    trial.messages.append(message)
    trial.save()
    try:
        trial.description = get_description(trial.survey_id, trial.segmentation, trial.segment_id, environ="staging")
    except FileNotFoundError as e:
        logger.error(e)
    except ValueError as e:
        logger.error(e)
    except Exception as e:
        logger.error(e)

    return trial, message


def process_add_message(trial_id, payload):
    trial = Trial.objects(trial_id=trial_id).first()
    if not trial:
        abort(400, description="Trial not found")

    segmentation = trial.segmentation
    segment = trial.segment
    segment_id = trial.segment_id
    survey_id = trial.survey_id
    seg_description = trial.description
    if not seg_description:
        seg_description = get_description(trial.survey_id, trial.segmentation, trial.segment_id, environ="staging")
        trial.description = seg_description
        trial.save(validate=False)
        trial.reload()

    question = payload["question"]
    messages = trial.messages
    message_list = []
    if len(messages) >= current_app.config["TRIAL_THRESHOLD"]:
        abort(400, "Trial has expired. You have reached the maximum amount of messages allowed")

    chatbot = Chatbot(
        openai_key=current_app.config["OPENAI_API_KEY"],
        question=question,
        survey_id=survey_id,
        segmentation=segmentation,
        segment_id=segment_id,
        segment_description=seg_description,
        messages=[],
    )
    if len(messages) == 1:
        messages = chatbot.generate_base_message([], [])
        for item in messages:
            message = Message(**item)
            message.is_visible = False
            message.is_bot = True
            trial.messages.append(message)
            # message_list.append(serialize_gpt_prompt(message))
        trial.save()
        trial.reload()

    for message in trial.messages:
        if message.role != "initial":
            message_list.append(serialize_gpt_prompt(message))

    chatbot.set_messages(message_list)

    question_message = create_trial_message(question, role="user", is_bot=False)
    trial.messages.append(question_message)
    trial.save()

    gpt_prompt = create_gpt_prompt(question, trial.survey, segment, chatbot)

    answer_message = create_trial_message(gpt_prompt, role="assistant", is_bot=True)
    trial.messages.append(answer_message)
    trial.save()

    response = {
        "question": serialize_trial_message(question_message),
        "message": serialize_trial_message(answer_message),
    }
    return response


def process_add_llm_message(trial_id, payload):
    trial = Trial.objects(trial_id=trial_id).first()
    if not trial:
        abort(400, description="Trial not found")

    # Check for trial message threshold
    if len(trial.messages) >= current_app.config["TRIAL_THRESHOLD"]:
        abort(400, description="Trial has expired. You have reached the maximum amount of messages allowed.")

    # Initialize data handlers
    data = {
        "segmentation": trial.segmentation,
        "segment": trial.segment,
        "segment_id": trial.segment_id,
        "survey_id": trial.survey_id,
        "survey": trial.survey,
    }
    data_handler, mongo_handler = _initialize_data_handlers(current_app.config, data)

    # Generate answer to the question
    question = payload["question"]
    history = _get_history_except_initial(trial) if len(trial.messages) > 1 else []
    question_generator = PythiaQuestionGenerator(data_handler, current_app.config["OPENAI_API_KEY"])
    answer = _generate_chatbot_response(question_generator, mongo_handler, question, history)

    # Create and append messages
    question_message = create_trial_message(question, role="user", is_bot=False)
    answer_message = create_trial_message(answer, role="assistant", is_bot=True)
    trial.messages.append(question_message)
    trial.messages.append(answer_message)
    trial.save()

    response = {
        "question": serialize_trial_message(question_message),
        "message": serialize_trial_message(answer_message),
    }
    return response


def _get_history_except_initial(trial):
    filtered_messages = [message for message in trial.messages if message.role != "initial"]
    return serialize_langchain_prompt_list(filtered_messages)


def create_trial_message(content, role, is_bot, is_visible=True):
    message = Message(
        content=content,
        role=role,
        is_bot=is_bot,
        is_visible=is_visible,
    )
    return message
