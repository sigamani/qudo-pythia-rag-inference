import os
import sys
import time
from datetime import timedelta

from colorama import Fore, init


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.settings.config import app_config
from app.utils.chatbot.langchain_bot import PythiaChatbot
from app.utils.chatbot.langchain_utils import (
    MongoDBHandler,
    PythiaDataHandler,
    PythiaQuestionGenerator,
)


# Read the environment variable
env = os.getenv("ENV", "staging")  # Default to 'development' if ENV is not set

# Select the appropriate configuration class based on the environment variable
config_class = app_config.get(env.lower(), app_config["staging"])

config = config_class()


def main():
    # User inputs for testing
    # survey_name = input("Enter survey name: ")
    # segmentation = input("Enter segmentation name: ")
    # segment = input("Enter segment name: ")
    survey_name = f"qudo_financialservices_usa_q1_2023_{config.S3_DS_ENVIRONMENT}"
    segmentation = "qudo_bank_switching_segmentation"
    segment = "Interest-led Switchers"
    gpt_model = "gpt-4"

    # Initialize data handler
    data_handler = PythiaDataHandler(survey_name, segmentation, segment, config.S3_DS_ENVIRONMENT)

    # Initialize MongoDB handler
    mongo_handler = MongoDBHandler(
        survey_name,
        segmentation,
        segment,
        config.MONGODB_ATLAS_CLUSTER_URI,
        config.OPENAI_API_KEY,
        config.MONGO_DB_URL,
        config.MONGO_PUBLIC_KEY,
        config.MONGO_PRIVATE_KEY,
        config.MONGO_CLUSTER,
        config.MONGO_GROUP_ID,
        data_handler,
    )

    # Initialize question generator
    question_generator = PythiaQuestionGenerator(data_handler, config.OPENAI_API_KEY)

    # Initialize chatbot
    chatbot = PythiaChatbot(
        gpt_model, openai_key=config.OPENAI_API_KEY, mongo_handler=mongo_handler, question_generator=question_generator
    )

    chat_history = []

    # User interaction loop
    while True:
        user_question = input(Fore.RED + "Enter your question (or 'exit' to quit): ")
        if user_question.lower() == "exit":
            break

        start_time = time.time()
        # Generate chatbot response
        response = chatbot.generate_chatbot()({"question": user_question, "chat_history": chat_history})
        answer = response["answer"]

        # Print the chatbot's answer
        print(Fore.GREEN + f"Chatbot's answer: {answer}")
        print("\n")

        end_time = time.time()
        query_time = str(timedelta(seconds=(end_time - start_time)))
        chat_history.append((response["question"], response["answer"]))


if __name__ == "__main__":
    init(autoreset=True)
    main()
