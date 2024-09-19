import json
import os
import sys
import concurrent.futures

import boto3
import botocore.exceptions
import s3fs

from app.settings.config import app_config
from app.utils.chatbot.langchain_utils import (
    MongoDBHandler,
    PythiaDataHandler,
)

# Read the environment variable
env = os.getenv("ENV", "staging")  # Default to 'development' if ENV is not set

# Select the appropriate configuration class based on the environment variable
config_class = app_config.get(env.lower(), app_config["staging"])

config = config_class()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_all_segments(s3_client, bucket):
    """
    Fetches all segments from essential columns files considering certain conditions from a S3 bucket.
    Parameters:
    s3_client: boto3 client for S3
    bucket: A string containing the name of the S3 bucket
    Returns:
    A generator of dictionaries that contain surveyname and segmentations_data
    """
    s3_prefix = "data-store/codebuild-resources/essential_columns/"
    paginator = s3_client.get_paginator('list_objects')
    # required_projects_key = ['zeitgeist', 'financialservices_usa', 'financialservices_uk', 'vodafone']
    required_projects_key = ['financialservicesfinal_uk']
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=s3_prefix):
            for content in page.get('Contents', []):
                key = content['Key']
                if 'essentialcolumns_' not in key.split('/')[-1]:
                    continue
                if not any(substring in key for substring in required_projects_key):
                    continue
                temp_file = s3_client.get_object(Bucket=bucket, Key=key)
                temp_essential_columns = json.load(temp_file['Body'])
                if 'segmentation_columns' not in temp_essential_columns.get('essential_columns', {}).keys():
                    continue
                temp_segmentations_data = [{x.get('segmentation_type', '').lower(): [*x['names'].values()]} for x in
                                           temp_essential_columns['essential_columns']['segmentation_columns']]
                if temp_essential_columns.get('project_name', '') == 'qudo_financialservicesfinal_uk_q1_2023':
                    temp_essential_columns['project_name'] = 'qudo_financialservices_uk_q1_2023'
                yield {
                    'surveyname': temp_essential_columns.get('project_name', ''),
                    'segmentations_data': temp_segmentations_data
                }
    except botocore.exceptions.BotoCoreError as e:
        print(f"Failed to list objects or fetch details due to error: {e}")


def process_segment(survey, segmentation_dict, config):
    if segmentation_dict:
        for segmentation, segments in segmentation_dict.items():
            for segment in segments:
                # survey_name = f"{survey['surveyname']}_{config.S3_DS_ENVIRONMENT}"
                survey_name = f"{survey['surveyname']}"
                data_handler = PythiaDataHandler(survey_name, segmentation, segment, config.S3_DS_ENVIRONMENT)
                survey_name = f"{survey['surveyname']}_{config.S3_DS_ENVIRONMENT}"
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
                mongo_handler.generate_and_save_vectors()

                create_index_response = mongo_handler.create_search_index()
                # print(create_index_response)

                if isinstance(create_index_response, dict) and create_index_response.get("error", None) == 400:
                    raise RuntimeError(
                        "Error in creating MongoDB collection and search index: ",
                        create_index_response["message"]
                    )


# could this be parallelised?
def gen_all_vector_collections(s3_client, bucket, max_workers=10):
    """
    The function `gen_all_vector_collections(s3_client, bucket)` generates and saves vectors
    for every segment in each segmentation from every survey data received
    from the `get_all_segments(s3_client, bucket)` function.
    """
    survey_meta_deta_list = get_all_segments(s3_client, bucket)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for survey in survey_meta_deta_list:
            for segmentation_dict in survey['segmentations_data']:
                futures.append(executor.submit(process_segment, survey, segmentation_dict, config))

        # Wait for all futures to complete
        concurrent.futures.wait(futures)


if __name__ == '__main__':
    s3 = boto3.resource("s3")
    s3_client = boto3.client("s3")
    s3_check = s3fs.S3FileSystem()

    bucket = 'qudo-datascience'

    gen_all_vector_collections(s3_client, bucket)
