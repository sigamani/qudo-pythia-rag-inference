import logging

from flask import abort
from openai.error import InvalidRequestError, RateLimitError

from app.utils.chatbot.gpt_utils.chatgpt_bot import Chatbot
from app.utils.chatbot.gpt_utils.information_retrieval import (
    compute_cosine_generate_mode_response,
    load_segment_q_embeddings_pop_modes,
)

logger = logging.getLogger("qudo")


def create_gpt_prompt(question: str, survey_name: str, segment: str, chatbot: Chatbot):

    ref_table, segment_pop_modes = load_segment_q_embeddings_pop_modes(
        survey_name, chatbot.get_segmentation(), segment, environ="staging"
    )
    relevant_questions, relevant_answers, cosine_results_df = compute_cosine_generate_mode_response(
        question, ref_table, segment_pop_modes, embedding_model="text-embedding-ada-002", cosine_threshold=0.85
    )

    if (
        len(cosine_results_df) > 0
        and cosine_results_df.iloc[0]["max_cosine_score"] > 0.95
        and cosine_results_df.iloc[0]["weighted_mode"] != "not selected"
    ):
        persona_answer = cosine_results_df.iloc[0]["weighted_mode"]
        survey_question = cosine_results_df.iloc[0]["title"]
        return persona_answer
    else:
        try:
            import time

            start_time = time.time()
            gpt_response = chatbot.query_chatgpt_bot(relevant_questions, relevant_answers)
            elapsed_time = time.time() - start_time

            logger.info(f"GPT Execution time: {elapsed_time} seconds")
            persona_answer = amend_response(gpt_response["answer"])
            return persona_answer
        except RateLimitError as e:
            logger.error(e)
            abort(400, description=e.error)
            return {"message": "The System is overloaded at the moment. Please try again a bit later."}
        except InvalidRequestError as e:
            logger.error(f"Error: {e}")
            abort(400, description=e.error)
        except Exception as e:
            logger.error(e)
            abort(400, description=repr(e))


replace_phrasing = {"As an AI language model, ": "I am a synthetic AI persona, as such "}


def amend_response(answer):
    for phrase_to_replace, replacement_phrase in replace_phrasing.items():
        answer = answer.replace(phrase_to_replace, replacement_phrase)
    return answer
