import ast
import pandas as pd
from langchain.chains import LLMChain
from langchain.llms.openai import OpenAI
from langchain.prompts import PromptTemplate
from .data_handler import PythiaDataHandler


class PythiaQuestionGenerator:
    def __init__(self, data_handler: PythiaDataHandler, openai_key: str):
        self.data_handler = data_handler
        self.openai_key = openai_key

    def generate_question_variations(self) -> pd.DataFrame:
        """
        Apply GPT model on original and better format questions to generate variations and document it

        Returns:
            DataFrame: A DataFrame containing the original question, new question format and its variations
        """

        questions_answers_df = pd.read_parquet(
            f"s3://qudo-datascience/data-store/pythia_outputs/{self.data_handler.environ}/questions_answers/{self.data_handler.survey_name}/{self.data_handler.segmentation_name}/{self.data_handler.segment_name}.parquet"
        )
        questions_df = questions_answers_df["question_text"].drop_duplicates().to_frame()
        original_questions_dict = [{"question": item} for item in questions_df["question_text"]]
        better_template = """
                   Transform the questions: {question} to be open-ended, concise, clear and coherent.
                   Do not include multiple specific pre-set answer options in the question.
                   Answer:
               """
        better_questions_results = self.generate_questions_from_template(original_questions_dict, better_template)
        questions_df["better_question"] = [x[0].text.strip().replace("\n", "") for x in better_questions_results]
        better_questions_dict = [{"question": item} for item in questions_df["better_question"]]
        variations_template = """
                   Provide three variations of the question: {question} without changing its meaning.
                   Do not include multiple specific pre-set answer options in the questions.
                   Return the results in a python list: ["<variation 1>", "<variation 2>", "<variation 3>"]
                   Answer:
               """

        variations_questions_results = self.generate_questions_from_template(better_questions_dict, variations_template)
        questions_df["test_question"] = [
            ast.literal_eval(x[0].text.strip().replace("\n", "")) for x in variations_questions_results
        ]
        questions_df = questions_df.explode(column="test_question")
        questions_df["label"] = "relevant"

        save_path = f"s3://qudo-datascience/data-store/pythia_outputs/{self.data_handler.environ}/question_variations/{self.data_handler.survey_name}/{self.data_handler.segmentation_name}/{self.data_handler.segment_name}.parquet"

        questions_df.to_parquet(save_path)
        return questions_df

    def generate_questions_from_template(self, questions_dict: list, template: str):
        """
        Generate questions using a specified GPT model and a configuration of questions dict and template.

        Parameters:
        questions_dict (dict): A dictionary containing the required context for questions generation.
        template (str): A format string specifying a desired structure for generated questions.

        Returns:
        `LLMChain.generations`: A list of generated questions based on the given template and context.
        """
        prompt = PromptTemplate(template=template, input_variables=["question"])
        llm = OpenAI(model_name="text-davinci-003", openai_api_key=self.openai_key)
        llm_chain = LLMChain(prompt=prompt, llm=llm)
        return llm_chain.generate(questions_dict).generations

    def setup_templates(self):
        """
        Returns chatbot prompt templates.

        Returns:
            Tuple with two templates for condensing questions and QA scenarios.
        """
        condense_question_template = """Given the following chat history and a follow up question,
                    rephrase the follow up input question to be a standalone question.
                    Or end the conversation if it seems like it's done.
                    Chat History:
                    {chat_history}
                    Follow Up Input:
                    {question}
                    Standalone question:"""
        qa_template = f"""You are PersonaGPT, the best persona bot ever!
                    We ran a market research survey and collected answers from respondents.
                    A segment emerged and you represent a segment of this survey, called '{self.data_handler.segment_name}'.
                    Use only the following context to answer the question.
                    Please create a response of up to 100 words and limit hallucinations.
                    Do not give any advice which could be illegal or violates personal data.
                    Context:
                    {{context}}
                    Question:
                    {{question}}
                    Helpful Answer:"""

        return condense_question_template, qa_template
