import logging

import certifi
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.mongodb_atlas import MongoDBAtlasVectorSearch
from pymongo import errors
from pymongo.mongo_client import MongoClient

from app.utils.atlas_api_utils import AtlasSearchUtils

from .data_handler import PythiaDataHandler

logger = logging.getLogger("qudo")


class MongoDBHandler:
    """
    A class used to handle MongoDB operations such as creating a client, creating a search index,
    validating and saving vectors, and generating and saving vectors.

        Attributes:
            ATLAS_VECTOR_SEARCH_INDEX_NAME (str): The name of the Atlas vector search index.

            DB_NAME (str): The name of the database.

            collection_name (str): The name of the collection.

            openai_key (str): The OpenAI API key.

            db_url (str): The MongoDB connection string.

            atlas_api (str): The Atlas API.

            cluster (str): The cluster name.

            mongo_public_key (str): The MongoDB public key.

            mongo_private_key (str): The MongoDB private key.

            group_id (str): The group ID.

            data_handler (PythiaDataHandler): The data handler object.

            client (MongoClient): The MongoDB client.

        Methods:
            _create_client(): Creates a MongoDB client.

            _get_atlas_client(): Gets an Atlas client.

            create_search_index(): Creates an Atlas search index.

            validate_and_save_vectors(data): Validates the collection and saves the vectors.

            save_vectors(data): Saves the vectors to the MongoDB collection.

            get_vector_store(): Gets the vector store.

            generate_and_save_vectors(): Generates and saves vectors to the MongoDB collection.
    """

    ATLAS_VECTOR_SEARCH_INDEX_NAME = "default_search_index"
    DB_NAME = "pythia-api-service"

    def __init__(
        self,
        survey_name,
        segmentation_name,
        segment_name,
        atlas_api,
        openai_key,
        db_url,
        mongo_public_key,
        mongo_private_key,
        cluster,
        group_id,
        data_handler: PythiaDataHandler,
    ):
        """
        The constructor for MongoDBHandler class.

        Args:
            survey_name (str): The survey name.
            segmentation_name (str): The segmentation name.
            segment_name (str): The segment name.
            atlas_api (str): The Atlas API.
            openai_key (str): The OpenAI API key.
            db_url (str): The MongoDB connection string.
            mongo_public_key (str): The MongoDB public key.
            mongo_private_key (str): The MongoDB private key.
            cluster (str): The cluster name.
            group_id (str): The group ID.
            data_handler (PythiaDataHandler): The data handler object.
        """
        self.collection_name = f"{survey_name}-{segmentation_name}-{segment_name}-pythia-embeddings"
        self.openai_key = openai_key
        self.db_url = db_url
        self.atlas_api = atlas_api
        self.cluster = cluster
        self.mongo_public_key = mongo_public_key
        self.mongo_private_key = mongo_private_key
        self.group_id = group_id
        self.data_handler = data_handler

        self.client = self._create_client()

    def _create_client(self):
        """
        Creates a MongoDB client.

        Returns:
            MongoClient: The created MongoDB client.
        """
        return MongoClient(self.db_url, tlsCAFile=certifi.where())

    def _get_atlas_client(self):
        """
        Gets an Atlas client.

        Returns:
            AtlasSearchUtils: The Atlas client.
        """
        return AtlasSearchUtils(self.mongo_public_key, self.mongo_private_key, self.group_id, self.cluster)

    def create_search_index(self):
        """
        Creates an Atlas search index if it does not exist.
        """
        if self._get_atlas_client().is_atlas_search_index_created(
            self.DB_NAME, self.collection_name, self.ATLAS_VECTOR_SEARCH_INDEX_NAME
        ):
            return

        logger.info(f"Creating Atlas Search index {self.ATLAS_VECTOR_SEARCH_INDEX_NAME}")

        return self._get_atlas_client().create_index(
            self.DB_NAME,
            self.collection_name,
            self.ATLAS_VECTOR_SEARCH_INDEX_NAME,
        )

    def validate_and_save_vectors(self, data):
        """
        Validates the collection and saves the vectors if the collection is empty or does not exist.

        Args:
            data (DataFrame): The data to save.
        """
        try:
            collection_exist = self.client[self.DB_NAME].validate_collection(self.collection_name)
            if collection_exist["nrecords"] == 0:
                self.save_vectors(data)
        except errors.OperationFailure:
            self.save_vectors(data)

    def save_vectors(self, data):
        """
        Saves the vectors to the MongoDB collection.

        Args:
            data (DataFrame): The data to save.
        """
        MongoDBAtlasVectorSearch.from_documents(
            documents=data,
            embedding=OpenAIEmbeddings(disallowed_special=(), openai_api_key=self.openai_key),
            collection=self.client[self.DB_NAME][self.collection_name],
            index_name=self.ATLAS_VECTOR_SEARCH_INDEX_NAME,
            # tlsCAFile=certifi.where(),
        )

    def get_vector_store(self):
        """
        Gets the vector store.

        Returns:
            MongoDBAtlasVectorSearch: The vector store.
        """
        return MongoDBAtlasVectorSearch.from_connection_string(
            self.db_url,
            f"{self.DB_NAME}.{self.collection_name}",
            OpenAIEmbeddings(disallowed_special=(), openai_api_key=self.openai_key),
            index_name=self.ATLAS_VECTOR_SEARCH_INDEX_NAME,
        )

    def generate_and_save_vectors(self):
        """
        Generates and saves vectors to the MongoDB collection.
        """
        data = self.data_handler.generate_questions_answers_df()
        self.validate_and_save_vectors(data)
