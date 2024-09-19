import os
import sys
import time
from datetime import timedelta

import pandas as pd
from colorama import init

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


def multiple_questions_pythia(questions_filepath: str, survey_name: str, segmentation_name: str, segment_name: str,
                gpt_model: str = 'gpt-4') -> pd.DataFrame:
    """
        Function to test the Pythia model. Measures average response time of the chatbot to each question in the list.
        Parameters:
            questions (list of str): List of questions for the chatbot to answer.
            survey_name (str): Name of the survey.
            segmentation_name (str): The named segmentation in use.
            segment_name (str): Name of the segment.
            gpt_model (str, optional): The model to use. Defaults to 'gpt-4'.
        Returns:
            results_df (DataFrame): A DataFrame containing the results of the test.
        """

    questions_csv = pd.read_csv(questions_filepath)
    questions = questions_csv['question']

    # Initialize data handler
    data_handler = PythiaDataHandler(survey_name, segmentation_name, segment_name, config.S3_DS_ENVIRONMENT)

    # Initialize MongoDB handler
    mongo_handler = MongoDBHandler(
        survey_name,
        segmentation_name,
        segment_name,
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
    pythia = PythiaChatbot(
        gpt_model, openai_key=config.OPENAI_API_KEY, mongo_handler=mongo_handler, question_generator=question_generator
    )
    chatbot = pythia.generate_chatbot()

    results_df = pd.DataFrame(columns=['test_question', 'response', 'query_time'])

    for question in questions:
        start_time = time.time()
        result = chatbot({"question": question, "chat_history": []})
        end_time = time.time()

        query_time = end_time - start_time
        row = {'test_question': result['question'], 'response': result['answer'],
               'query_time': timedelta(seconds=query_time)}
        results_df = results_df.append(row, ignore_index=True)
        print('\n')

    results_df['survey_name'] = survey_name
    results_df['segmentation'] = segmentation_name
    results_df['segment'] = segment_name
    results_df['model'] = gpt_model
    results_df['query_time'] = pd.to_timedelta(results_df['query_time'])
    mean_response_times = results_df['query_time'].mean()
    print(f'Mean response time for {gpt_model} is {str(mean_response_times).split()[-1]}.')
    results_df.to_parquet(
        f'{survey_name}_{segmentation_name}_{segment_name}_{config.S3_DS_ENVIRONMENT}_{gpt_model}_pythia_results.parquet')
    return results_df


if __name__ == "__main__":
    init(autoreset=True)
    survey_name = f'qudo_consumerzeitgeist_uk_q2_2023_trav_{config.S3_DS_ENVIRONMENT}'
    segmentation_name = 'qudo_attitudinal'
    segment_name = 'Reluctant Nomads'
    gpt_model = 'gpt-4'
    questions_filepath = 'test.csv'
    multiple_questions_pythia(questions_filepath, survey_name, segmentation_name, segment_name, gpt_model=gpt_model)
