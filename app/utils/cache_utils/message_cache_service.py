import json
import logging

from flask import abort
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.blueprints.conversations.service import fetch_conversations
from app.blueprints.messages.serializer import (
    serialize_gpt_prompt_list,
    serialize_langchain_prompt_list,
)
from app.utils.chatbot.gpt_utils.information_retrieval import get_description

logger = logging.getLogger("qudo")


class MessageCacheService:
    def __init__(self):
        self.timeout = 1800
        self.decoded_values = self.get_decoded_values()

    @staticmethod
    def get_decoded_values():
        decoded_values = {"payload": get_jwt(), "sub": get_jwt_identity()}
        return decoded_values

    def get_data(self, conversation_id):
        from app.utils.redis_util import RedisUtil

        data = RedisUtil.get_cached_data(f"token_sub__{self.decoded_values['sub']}__{conversation_id}")
        if not data:
            logger.info("data from db")
            conversation = fetch_conversations({"id": conversation_id})
            if not conversation:
                abort(400, description="Conversation doesn't exists")
            conversation = conversation.get()
            logger.info(conversation.to_json())
            data = {
                "segmentation": conversation.segmentation,
                "segment": conversation.segment,
                "segment_id": conversation.segment_id,
                "survey_id": conversation.survey_id,
                "survey": conversation.survey,
            }

            from app.blueprints.messages.service import fetch_messages

            messages = fetch_messages({"conversation_id": conversation_id, "role__not__in": ["initial"]})

            data["messages"] = serialize_gpt_prompt_list(messages)
            data["history"] = serialize_langchain_prompt_list(messages)

            try:
                data["seg_description"] = get_description(
                    conversation.survey_id, conversation.segmentation, conversation.segment_id, environ="staging"
                )
            except FileNotFoundError as e:
                logger.error(e)
            except ValueError as e:
                logger.error(e)
            except Exception as e:
                logger.error(e)

            self.set_data(conversation_id, data)

        else:
            logger.info("data from redis cache")
            data = str(data, "utf-8")
            data = json.loads(data)
            data["history"] = [tuple(item) for item in data["history"]]
        return data

    def set_data(self, conversation_id, data):
        from app.utils.redis_util import RedisUtil

        data = json.dumps(data)
        RedisUtil.set_cache_data(f"token_sub__{self.decoded_values['sub']}__{conversation_id}", data, self.timeout)

    def invalidate_cache(self):
        from app.utils.redis_util import RedisUtil

        RedisUtil.invalidate_cache_data("token_sub__%s" % self.decoded_values["sub"])
