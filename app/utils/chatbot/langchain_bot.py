import openai
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

from app.utils.chatbot.langchain_utils.mongo_utils import MongoDBHandler
from app.utils.chatbot.langchain_utils.question_generator import PythiaQuestionGenerator


class PythiaChatbot:
    def __init__(
        self, gpt_model: str, openai_key: str, mongo_handler: MongoDBHandler, question_generator: PythiaQuestionGenerator
    ):
        self.gpt_model = gpt_model
        self.openai_key = openai_key
        self.mongo_handler = mongo_handler
        self.question_generator = question_generator
        openai.api_key = openai_key

    def _build_non_streaming_chatbot(self, temperature: float):
        """
        Initiates non-streaming chatbot.

        Returns:
            Non-streaming chatbot based on the provided specifications.
        """
        return ChatOpenAI(temperature=temperature, model_name=self.gpt_model, openai_api_key=self.openai_key)

    def _build_chatbot(self, temperature: float, max_tokens: float):
        """
        Initiates chatbot.

        Returns:
            Chatbot based on the provided specifications.
        """
        return ChatOpenAI(
            streaming=False,
            verbose=True,
            temperature=temperature,
            max_tokens=max_tokens,
            model_name=self.gpt_model,
            openai_api_key=self.openai_key,
        )

    def generate_chatbot(self) -> ConversationalRetrievalChain:
        """
        This function generates a chatbot using GPT, MongoDBAtlasVectorSearch and several templates.
        The temperature, max_tokens and model_name used by the conversational bot are defined within the function.

        Only the MongoDB Atlas cluster URI, database and collection names need to be provided externally.
        Returns:
            chatbot: A ConversationalRetrievalChain instance.
        """
        temperature = 0
        max_tokens = 150

        self.mongo_handler.generate_and_save_vectors()

        create_index_response = self.mongo_handler.create_search_index()

        if isinstance(create_index_response, dict) and create_index_response.get("error", None) == 400:
            raise RuntimeError(
                "Error in creating MongoDB collection and search index: ", create_index_response["message"]
            )

        # Storage for vector content retrieved from MongoDB
        vectorstore = self.mongo_handler.get_vector_store()

        # Templates for prompts
        condense_question_template, qa_template = self.question_generator.setup_templates()

        # Prompts from the templates
        condense_question_prompt = PromptTemplate.from_template(condense_question_template)
        qa_prompt = PromptTemplate.from_template(qa_template)

        # Initialize chatbot model objects
        llm_1 = self._build_non_streaming_chatbot(temperature)
        llm_2 = self._build_chatbot(temperature, max_tokens)

        # Create chain for generating questions and documents
        question_generator = LLMChain(llm=llm_1, prompt=condense_question_prompt)
        doc_chain = load_qa_chain(llm=llm_2, chain_type="stuff", prompt=qa_prompt)

        # Configure and return chatbot
        chatbot = ConversationalRetrievalChain(
            retriever=vectorstore.as_retriever(), combine_docs_chain=doc_chain, question_generator=question_generator
        )
        return chatbot
