import logging

import openai
import tiktoken
from tenacity import retry, stop_after_attempt, wait_random_exponential

logger = logging.getLogger("qudo")


class Chatbot:
    """
    A class representing a chatbot.

        Attributes:
            openai_key (str): The OpenAI API key.
            question (str): The main question to ask the chatbot.
            survey_id (int): The ID of the survey.
            segmentation (str): The name of the segmentation.
            segment_id (int): The ID of the segment.
            segment_description (str): The description of the segment.
            messages (list): The list of messages exchanged in the conversation.
    """

    def __init__(self, openai_key, question, survey_id, segmentation, segment_id, segment_description, messages):
        """
        Initializes a Chatbot instance.

        Args:
            openai_key (str): The OpenAI API key.
            question (str): The main question to ask the chatbot.
            survey_id (int): The ID of the survey.
            segmentation (str): The name of the segmentation.
            segment_id (int): The ID of the segment.
            segment_description (str): The description of the segment.
            messages (list): The list of messages exchanged in the conversation.
        """
        openai.api_key = openai_key
        self.question = question
        self.survey_id = survey_id
        self.segmentation = segmentation
        self.segment_id = segment_id
        self.segment_description = segment_description
        self.messages = messages
        self.openai_key = openai_key

    def set_question(self, question):
        self.question = question

    def get_question(self):
        return self.question

    def set_survey_id(self, survey_id):
        self.survey_id = survey_id

    def get_survey_id(self):
        return self.survey_id

    def set_segmentation(self, segmentation):
        self.segmentation = segmentation

    def get_segmentation(self):
        return self.segmentation

    def set_segment_id(self, segment_id):
        self.segment_id = segment_id

    def get_segment_id(self):
        return self.segment_id

    def set_segment_description(self, segment_description):
        self.segment_description = segment_description

    def get_segment_description(self):
        return self.segment_description

    def set_messages(self, messages):
        self.messages = messages

    def get_messages(self):
        return self.messages

    @retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(3))
    def generate_base_message(self, response_questions, response_answers):
        """
        Generates the base message for the chatbot.

        Args:
            response_questions (list): The list of response questions.
            response_answers (list): The list of response answers.

        Returns:
            list: The generated base message.
        """
        if response_questions and response_answers:

            relevant_question_answers_list = list(map(self._get_extra_questions, response_questions, response_answers))
            relevant_question_answer = " ".join(relevant_question_answers_list)
        else:
            relevant_question_answer = ""

        messages = [
            {"role": "system", "content": "You are personaGPT, the best persona generating AI ever"},
            {
                "role": "assistant",
                "content": f"We conducted a survey and you represent a segment of this survey. "
                f"This segment is described as: {self.segment_description}.",
            },
            {
                "role": "assistant",
                "content": f"I want you to respond as this segment to the following "
                f"question: "
                f'"{self.question}". Please create a response of up to 100 words and '
                f"limit hallucinations, and do not go beyond answering the question. "
                f"Do not give any advice which could be illegal "
                f"or violates personal data. {relevant_question_answer}"
                f"You do not need to reintroduce yourself after the first time.",
            },
        ]
        return messages

    @retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(3))
    def query_chatgpt_bot(self, response_questions, response_answers, gpt_model="gpt-4"):
        mod_check = openai.Moderation.create(input=self.question)
        if not self.messages:
            self.messages = self.generate_base_message(response_questions, response_answers)

        if response_questions and response_answers:
            relevant_question_answers_list = list(map(self._get_extra_questions, response_questions, response_answers))
            relevant_question_answer = " ".join(relevant_question_answers_list)
            self.question = self.question + relevant_question_answer

        new_question_message = {"role": "user", "content": self.question}

        self.messages.append(new_question_message)

        if not mod_check["results"][0]["flagged"]:
            answer = openai.ChatCompletion.create(
                model=gpt_model,
                messages=self.messages,
                max_tokens=self.count_tokens(model=gpt_model),
                temperature=0.3,
            )
            logger.info(answer)
            answer = answer["choices"][0]["message"]["content"]
        else:
            answer = "I cannot give inappropriate responses"

        self.messages.append({"role": "assistant", "content": answer})
        response = {
            "question": self.question,
            "moderated": True,
            "answer": answer,
            "messages": self.messages,
            "segment_description": self.segment_description,
        }

        return response

    def _get_extra_questions(self, response_question, response_answer):
        return (
            f'For reference, this segment responded to this question "{response_question}" with '
            f'this answer "{response_answer}".'
        )

    def count_tokens(self, model):
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")

        tokens_per_message = 3
        tokens_per_name = 1

        num_tokens = 0
        for message in self.messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        logger.info(f"Total tokens: {num_tokens}")
        return num_tokens
