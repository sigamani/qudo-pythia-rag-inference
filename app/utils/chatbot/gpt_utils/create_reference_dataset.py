import ast
import json
import re

import boto3
import openai
import pandas as pd
import s3fs
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from .dataset_helper_functions import (
    get_embedding,
    remove_contraction_apostraphes,
    ambiguous_title_fixer,
    extra_title_fixer,
    split_list,
)

s3 = boto3.resource("s3")
s3_client = boto3.client("s3")
s3_check = s3fs.S3FileSystem()

bucket = "qudo-datascience"

survey_name = "qudo_financialservices_usa_q1_2023_staging"
segmentation = "qudo_borrowing_segmentation"
segment = "qudo_borrowing_segmentation_Convenience Seekers"
environ = "staging"
gpt_model = "gpt-3.5-turbo"
embedding_model = "text-embedding-ada-002"
cosine_threshold = 0.85
input_question = "What is your credit score?"


@retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(3))
def generate_pythia_relevant_q_embeddings_survey(
    survey_name, environ="staging", gpt_model="gpt-3.5-turbo", embedding_model="text-embedding-ada-002"
):
    """Function to create test dataset for a segmentation. For a given segment:
    - We take the chi2 questions, transform them into "better" english.
    - For each of those questions, we generate three wording variations.
    - Generate n irrelevant questions to an example persona description of a segmentation.
    - Upload this dataset to S3.
    """

    r_question_bank = pd.read_parquet(
        f"s3://qudo-datascience/data-store/surveys/{environ}/questions_preprocessed/{survey_name}/{survey_name}.parquet"
    )

    undesired_categories = ["att", "qudo", "ref"]

    question_bank = r_question_bank[~r_question_bank["category"].isin(undesired_categories)].copy()

    question_bank["original_title"] = question_bank["title"].copy()

    question_bank["title"] = question_bank["title"].str.replace(
        "Of the two, please pick the picture that you prefer more.", "What is your visual style preference?"
    )
    question_bank["title"] = question_bank["title"].str.replace(
        "How much do you trust the following", "How much do you trust the following financial organisations"
    )
    question_bank["title"] = question_bank.apply(extra_title_fixer, axis=1)
    question_bank["title"] = question_bank["title"].str.replace("\xa0", "")

    question_bank["title"] = question_bank.apply(ambiguous_title_fixer, axis=1)
    question_bank["title"] = question_bank.apply(
        lambda x: x["title"] + ": " + x["option_text"] if "technologyacceptancemodel" in x["shortname"] else x["title"],
        axis=1,
    )

    remove_from_question = [
        " Please select all that apply.",
        " Please select all that apply or skip if none are applicable.",
        " Skip if none apply.",
        " Skip if none are applicable.",
        "Skip if none are applicable.",
        " Skip if none is applicable.",
        "Skip if none is applicable.",
        " or skip if none are applicable.",
        "or skip if none are applicable.",
        "of skip if none are applicable.",
        "or skip if not applicable.",
        "or skip if not applicable",
        " Select all that apply.",
        " Select all that apply",
        " Please skip if none apply.",
        " Pick up to two answers.",
        " You can pick up to three answers.",
        " You can pick your top one or two answers.",
        " You can pick one or two answers.",
        " Select all that is true in your case, or skip if none apply.",
        " Please select up to two items",
        " Please select up to two",
        " Select up to two options.",
        " Select all that describe your preferences",
        " Please pick up to two that you like the most.",
    ]

    for q in remove_from_question:
        question_bank["title"] = question_bank["title"].str.replace(q, "")

    shortname_title_mapping = question_bank[["shortname", "original_title", "title"]].copy().drop_duplicates()

    raw_questions = [tuple(x) for x in shortname_title_mapping[["shortname", "title"]].to_numpy()]
    raw_questions_split = split_list(raw_questions, 20)

    relevant_questions_dfs = []
    for sublist in raw_questions_split:
        better_completion = openai.ChatCompletion.create(
            model=gpt_model,
            messages=[
                {
                    "role": "system",
                    "content": "I will supply you a python list of tuples in the following format [(<id>, <original question>)]. Transform each <original question> to be open-ended, concise, clear and coherent, <transformed question>. Do not include multiple specific pre-set answer options in the questions. Please return the results in a python list of tuples: [(<id>, <original question>, <transformed question>)].",
                },
                {"role": "user", "content": str(sublist)},
            ],
        )

        better_questions = better_completion["choices"][0]["message"]["content"]
        try:
            temp_df = pd.DataFrame(ast.literal_eval(better_questions))
        except:
            temp_df = pd.DataFrame(ast.literal_eval(remove_contraction_apostraphes(better_questions)))

        relevant_questions_df = pd.DataFrame(sublist, columns=["shortname", "title"])
        relevant_questions_df["better_question"] = temp_df.iloc[:, -1:].copy()
        relevant_questions_df["better_question_embedding"] = relevant_questions_df["better_question"].apply(
            lambda x: get_embedding(x, model=embedding_model)
        )
        relevant_questions_dfs.append(relevant_questions_df)

    question_embeddings = pd.concat(relevant_questions_dfs)
    question_embeddings_full = shortname_title_mapping.merge(question_embeddings, on=["shortname", "title"])
    question_embeddings_full["title_embedding"] = question_embeddings_full["title"].apply(
        lambda x: get_embedding(x, model=embedding_model)
    )
    question_embeddings_full.to_parquet(
        f"s3://qudo-datascience/data-store/pythia_exploration/{environ}/{survey_name}/relevant_questions_embedding.parquet"
    )


def get_segment_name_id(survey_name, input_segmentation, input_segment=None, input_segment_id=None):
    rep = {"_staging": "", "_prod": "", "_test": ""}

    rep = dict((re.escape(k), v) for k, v in rep.items())

    pattern = re.compile("|".join(rep.keys()))

    survey_name_core = pattern.sub(lambda m: rep[re.escape(m.group(0))], survey_name)

    essential_columns_key = f"data-store/codebuild-resources/essential_columns/essentialcolumns_{survey_name_core}.json"

    if s3_check.exists(f"s3://{bucket}/{essential_columns_key}"):
        essential_columns_file = s3_client.get_object(Bucket=bucket, Key=essential_columns_key)
        essential_columns = json.load(essential_columns_file["Body"])
        segmentations_metadata = essential_columns["essential_columns"]["segmentation_columns"]
        segment_ids = [
            x["names"] for x in segmentations_metadata if x["segmentation_type"].lower() == input_segmentation
        ][0]
        segment_ids_df = pd.DataFrame.from_dict(segment_ids, orient="index").reset_index()
        segment_ids_df.columns = ["segment_id", "segment"]

        if (input_segment is None) and (input_segment_id is not None):
            temp_desired_data = segment_ids_df[segment_ids_df["segment_id"] == input_segment_id]["segment"].iloc[0]
            desired_data = input_segmentation + "_" + temp_desired_data
        elif (input_segment is not None) and (input_segment_id is None):
            proper_segment_name = input_segment.split("_")[-1]
            desired_data = segment_ids_df[segment_ids_df["segment"] == proper_segment_name]["segment_id"].iloc[0]
        else:
            raise ValueError("Input EITHER a segment id OR segment name to retrieve missing info.")

        return desired_data
    else:
        raise FileNotFoundError(f"Essential Columns file not found for {survey_name}. Check S3 or survey name.")


if __name__ == "__main__":
    get_segment_name_id(survey_name, "qudo_borrowing_segmentation", input_segment=segment)
    get_segment_name_id(survey_name, "qudo_borrowing_segmentation", input_segment_id="13243")
    generate_pythia_relevant_q_embeddings_survey(
        survey_name, environ=environ, gpt_model=gpt_model, embedding_model=embedding_model
    )
