import time
from datetime import timedelta

import pandas as pd
from openai.embeddings_utils import cosine_similarity

from app.utils.s3_utils import S3Utils

from ...mapping_utils import Mapping
from .dataset_helper_functions import get_embedding


def load_segment_q_embeddings_pop_modes(survey_name, segmentation, segment, environ="staging"):
    cluster_name = segment.split("_")[-1]
    survey_q_embeddings = pd.read_parquet(
        f"s3://qudo-datascience/data-store/pythia_exploration/{environ}/{survey_name}/relevant_questions_embedding.parquet"
    )
    segmentation_pop_modes = pd.read_parquet(
        f"s3://qudo-datascience/data-store/pythia_exploration/{environ}/{survey_name}/population_modes/{segmentation}/population_modes.parquet"
    )

    cluster_pop_modes = segmentation_pop_modes[segmentation_pop_modes["cluster"] == cluster_name].copy()

    segment_shortnames = cluster_pop_modes["shortname"].unique().tolist()

    cluster_q_embeddings = survey_q_embeddings[survey_q_embeddings["shortname"].isin(segment_shortnames)].copy()

    return cluster_q_embeddings, cluster_pop_modes


def compute_cosine_generate_mode_response(
    input_question, ref_table, pop_modes, embedding_model="text-embedding-ada-002", cosine_threshold=0.85
):
    start_time = time.time()
    input_question_embed = get_embedding(input_question, model=embedding_model)
    temp_ref = ref_table.copy()
    temp_ref["better_cosine_score"] = temp_ref["better_question_embedding"].apply(
        lambda x: cosine_similarity(x, input_question_embed)
    )
    temp_ref["title_cosine_score"] = temp_ref["title_embedding"].apply(
        lambda x: cosine_similarity(x, input_question_embed)
    )
    temp_ref["max_cosine_col"] = temp_ref[["better_cosine_score", "title_cosine_score"]].idxmax(axis=1)
    temp_ref["max_cosine_score"] = temp_ref[["better_cosine_score", "title_cosine_score"]].max(axis=1)
    temp_ref.sort_values(by=["max_cosine_score"], ascending=False, inplace=True)
    temp_ref = temp_ref.merge(pop_modes[["shortname", "weighted_mode", "unweighted_mode"]], on="shortname")

    similar_temp_ref = temp_ref[temp_ref["max_cosine_score"] >= cosine_threshold].reset_index(drop=True)

    if not similar_temp_ref.empty:

        result_answers = similar_temp_ref["weighted_mode"].to_list()
        result_questions = similar_temp_ref["title"].to_list()

    else:
        result_answers = []
        result_questions = []

        # top_question = temp_ref['title'].iloc[0]
        # top_answer = temp_ref['weighted_mode'].iloc[0]
        # top_cosine = round(temp_ref['max_cosine_score'].iloc[0], 2)

    end_time = time.time()
    query_time = str(timedelta(seconds=(end_time - start_time)))
    print(f"Query took {query_time}")

    return result_questions, result_answers, similar_temp_ref


def get_description(survey_id, segmentation_name, segment_id, environ, industry=None):
    bucket = "qudo-assets"
    segment_json_uri = f"data/{environ}/{str(survey_id)}/{segmentation_name}/segments.json"
    s3utils = S3Utils(bucket=bucket, environ=environ)

    if industry and industry.lower() in Mapping.INDUSTRY_MAPPING:
        industry = Mapping.INDUSTRY_MAPPING[industry.lower()]
        segment_json_uri = f"data/{environ}/{survey_id}/{industry}/{segmentation_name}/segments.json"

    if s3utils.is_valid_uri(segment_json_uri):
        segment_dict = s3utils.read_file(segment_json_uri)
        for segment in segment_dict["segments"]:
            if segment["id"] == str(segment_id):
                return segment["description"]
        raise ValueError("Cannot find segment description in the segments json.")
    else:
        raise FileNotFoundError("Cannot find the segments.json for this item, check the input parameters.")
