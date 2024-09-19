import pandas as pd
from langchain.document_loaders import DataFrameLoader

from app.utils.chatbot.helper_utils.data_utils import convert_to_shortname, load_parquet
from app.utils.s3_utils import S3Utils


class PythiaDataHandler:
    Q_CODE = "q_code"
    TITLE = "title"
    MODE = "mode"
    WEIGHTED_CATEGORY_PERCENTAGES = "weighted_category_percentages"
    CATEGORY_PERCENTAGES = "category_percentages"
    REPLACE_PATTERN = "_gg|_fb"

    def __init__(self, survey_name: str, segmentation_name: str, segment_name: str, environ: str):
        self.survey_name = survey_name + f"_{environ}"
        self.segmentation_name = segmentation_name
        self.segment_name = segment_name
        self.environ = environ
        self.s3utils = S3Utils(bucket="qudo-datascience", environ=environ)

        # Load data
        self.seg_modes_data = self._load_seg_modes_data()
        self.chisquared_data = self._load_chisquared_data()

    def _load_data(self, filepath: str, segment_filter: bool = False) -> pd.DataFrame:
        """
        Load data from a parquet file and perform preprocessing. If segment_filter is True,
        filter the data by segment name and update the category percentages column.

        Args:
            filepath (str): The path to the parquet file to load.
            segment_filter (bool, optional): A flag to determine whether to filter the data by segment name. Defaults to False.

        Returns:
            pd.DataFrame: The loaded and preprocessed data.

        Note:
            This function will modify the Q_CODE column by replacing the REPLACE_PATTERN with an empty string.
            If segment_filter is True, it will also modify the category percentages column by dividing each value by 100
            and rounding to 2 decimal places, and then apply the _update_smc_percentage function to the column.
        """

        data = load_parquet(filepath)
        data[self.Q_CODE] = data[self.Q_CODE].str.replace(self.REPLACE_PATTERN, "", regex=True)

        if segment_filter:
            data = data[data["segment"] == self.segment_name].copy()
            self.category_percentages_col = (
                self.WEIGHTED_CATEGORY_PERCENTAGES
                if self.WEIGHTED_CATEGORY_PERCENTAGES in data.columns
                else self.CATEGORY_PERCENTAGES
            )
            data[self.category_percentages_col] = data[self.category_percentages_col].apply(
                lambda x: [round(i / 100, 2) for i in x]
            )
            data[self.category_percentages_col] = data.apply(
                self._update_smc_percentage, args=(self.category_percentages_col,), axis=1
            )

        return data

    def _prep_data(self, data, qtype) -> pd.DataFrame:
        data_grouped = data.groupby([self.Q_CODE, self.TITLE])[self.category_percentages_col].apply(list).reset_index()
        data_grouped[self.category_percentages_col] = data_grouped[self.category_percentages_col].apply(
            lambda x: [item for sublist in x for item in sublist]
        )
        seg_modes_chi_squared = self.seg_modes_data[self.seg_modes_data["qtype"] == qtype][
            [self.Q_CODE, self.TITLE, self.MODE]
        ].merge(
            data_grouped[[self.Q_CODE, self.category_percentages_col, self.TITLE]],
            how="outer",
            on=[self.Q_CODE, self.TITLE],
        )
        return seg_modes_chi_squared

    def _load_seg_modes_data(self) -> pd.DataFrame:
        filepath = f"s3://qudo-datascience/data-store/pythia_exploration/{self.environ}/{self.survey_name}/{self.segmentation_name}/{self.segment_name}/segment_modes/segment_modes.parquet"
        # print(filepath)
        seg_modes_data = self._load_data(filepath)
        proportions = (seg_modes_data["proportion"].round(2)).astype(str)
        seg_modes_data[self.MODE] = seg_modes_data[self.MODE] + " (proportion of respondents: " + proportions + ")"
        return seg_modes_data

    def _load_chisquared_data(self):
        rule_based_filepath = f"data-store/sophos_outputs/{self.environ}/chisquared_preprocessed/{self.survey_name}/{self.segmentation_name}/rules_based.parquet"
        file_path = f"s3://qudo-datascience/data-store/sophos_outputs/{self.environ}/chisquared_preprocessed/{self.survey_name}/{self.segmentation_name}.parquet"

        if self.s3utils.is_valid_uri(rule_based_filepath):
            rule_based_filepath = f"s3://qudo-datascience/{rule_based_filepath}"
            return self._load_data(rule_based_filepath, segment_filter=True)
        return self._load_data(file_path, segment_filter=True)

    def _prep_varnames_seg_modes_chi_squared(self) -> pd.DataFrame:
        return self._prep_data(self.chisquared_data, "varname")

    def _prep_shortnames_seg_modes_chi_squared(self, varnames_to_shortname: set) -> pd.DataFrame:
        # chisquared_data_shortnames = self.chisquared_data.loc[
        #     self.chisquared_data[self.Q_CODE].isin(varnames_to_shortname)
        # ].copy()
        # chisquared_data_shortnames["shortname"] = chisquared_data_shortnames[self.Q_CODE].apply(convert_to_shortname)
        # replacement_dict = {"sbeh_us_insuranceownership_cb": "sbeh_us_insuranceintenders_cb"}
        # chisquared_data_shortnames["shortname"].replace(replacement_dict, inplace=True)
        # chisquared_data_shortnames.rename(columns={"shortname": self.Q_CODE}, inplace=True)
        # return self._prep_data(chisquared_data_shortnames, "shortname")
        chisquared_data_shortnames = self.chisquared_data.loc[
            self.chisquared_data["q_code"].isin(varnames_to_shortname)
        ].copy()
        chisquared_data_shortnames["shortname"] = chisquared_data_shortnames["q_code"].apply(convert_to_shortname)

        replacement_dict = {"sbeh_us_insuranceownership_cb": "sbeh_us_insuranceintenders_cb"}
        chisquared_data_shortnames["shortname"].replace(replacement_dict, inplace=True)

        chisquared_data_shortnames = (
            chisquared_data_shortnames.groupby(["shortname", "title"])[self.category_percentages_col]
            .apply(list)
            .reset_index()
        )
        chisquared_data_shortnames[self.category_percentages_col] = chisquared_data_shortnames[
            self.category_percentages_col
        ].apply(lambda x: [item for sublist in x for item in sublist])

        chisquared_data_shortnames.rename(columns={"shortname": "q_code"}, inplace=True)

        shortnames_seg_modes_chi_squared = self.seg_modes_data.loc[
            self.seg_modes_data["qtype"] == "shortname", ["q_code", "title", "mode"]
        ].merge(
            chisquared_data_shortnames[["q_code", self.category_percentages_col, "title"]],
            how="outer",
            on=["q_code", "title"],
        )
        return shortnames_seg_modes_chi_squared

    def _update_smc_percentage(self, row, cat_per_col: str) -> list:
        """
        Updates 'sig_more_category_percentage' with respondent proportion information.
        :param row: DataFrame row
        :param cat_per_col: category percentages column name
        :return: list with updated 'sig_more_category_percentage' data
        """
        return [
            f'{row["sig_more_category"][i]} (proportion of respondents: {row[cat_per_col][i]})'
            for i in range(len(row["sig_more_category"]))
        ]

    def generate_questions_answers_data(self) -> pd.DataFrame:
        """
        Main method for preparing the segmentation modes and chisquared significant answers for each question.
        The chi-squared data is identified via qcodes, which is a mix of varnames and shortnames.
        We attempt to process the varnames and then the shortnames
        """

        varnames_seg_modes_chi_squared = self._prep_varnames_seg_modes_chi_squared()

        varnames_to_shortname = set(
            varnames_seg_modes_chi_squared[pd.isna(varnames_seg_modes_chi_squared["mode"])]["q_code"]
        )

        shortnames_seg_modes_chi_squared = self._prep_shortnames_seg_modes_chi_squared(varnames_to_shortname)

        varnames_seg_modes_chi_squared.dropna(subset=["mode"], inplace=True)

        final_seg_modes_chi_squared = pd.concat([shortnames_seg_modes_chi_squared, varnames_seg_modes_chi_squared])
        final_seg_modes_chi_squared["title"] = final_seg_modes_chi_squared["title"].apply(
            lambda x: str(x).replace("\xa0", "")
        )

        return final_seg_modes_chi_squared

    def convert_to_questions_jsons(self, x: dict) -> dict:
        """
        Converts a dictionary into a specific format related to questions.
        Args:
            x (dict): The input dictionary that needs to be converted.
        Returns:
            dict: A dictionary with keys as 'question_text', 'modal_answer',
                and 'significant_answers' from the input data.
        """

        significant_answers = ""

        if isinstance(x.get(self.category_percentages_col), list):
            significant_answers = "; ".join(x[self.category_percentages_col])

        return {
            "question_text": x.get("title", ""),
            "modal_answer": x.get("mode", ""),
            "significant_answers": significant_answers,
        }

    def generate_questions_answers_df(self):
        """
        This method is used to generate and save vectors.
        It generates questions and answers data, converts these data to a specific JSON formatted data.
        Then it transforms these JSON data into pandas DataFrame and loads into MongoDB.
        Finally, it saves the data into an S3 bucket in parquet format.

        Returns:
        DataFrame: The final DataFrame object that consists of the questions and answers data.
        """
        final_pop_modes_chi_squared = self.generate_questions_answers_data()
        question_jsons = final_pop_modes_chi_squared.apply(self.convert_to_questions_jsons, axis=1)

        segment_json = {"segment_name": self.segment_name, "questions": question_jsons.to_list()}

        questions_answers_df = pd.DataFrame(segment_json["questions"])
        questions_answers_df["text"] = questions_answers_df.apply(
            lambda x: f"Survey Question: {x['question_text']}\nModal Answers: {x['modal_answer']}\nSignificant "
            f"Answers: {x['significant_answers']}",
            axis=1,
        )

        data = DataFrameLoader(questions_answers_df).load()
        questions_answers_df.to_parquet(
            f"s3://qudo-datascience/data-store/pythia_outputs/{self.environ}/questions_answers/{self.survey_name}"
            f"/{self.segmentation_name}/{self.segment_name}.parquet"
        )
        return data
