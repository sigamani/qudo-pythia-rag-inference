import logging

import requests
from flask import current_app
from requests.auth import HTTPDigestAuth

logger = logging.getLogger("qudo")


class AtlasSearchUtils:
    def __init__(self, username: str, password: str, group_id: str, cluster_name: str):
        self.base_url = "https://cloud.mongodb.com/api/atlas/v1.0"
        self.headers = {"Content-Type": "application/json"}
        self.auth = HTTPDigestAuth(username, password)
        self.group_id = group_id
        self.cluster_name = cluster_name

    def create_index(self, db_name, collection_name, index_name):
        """
        Create an Atlas Search index.

        Args:
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        index_name (str): The name for the new Atlas Search index.

        Returns:
        Response JSON from the Atlas API.
        """
        api_url = f"{self.base_url}/groups/{self.group_id}/clusters/{self.cluster_name}/fts/indexes"
        index_definition = {
            "collectionName": collection_name,
            "database": db_name,
            "mappings": {
                "dynamic": True,
                "fields": {"embedding": {"dimensions": 1536, "similarity": "cosine", "type": "knnVector"}},
            },
            "name": index_name,
        }

        response = requests.post(api_url, json=index_definition, auth=self.auth, headers=self.headers)
        logger.info(response.json())
        return response.json()

    def is_atlas_search_index_created(self, db_name, collection_name, index_name):
        """
        Check if an Atlas Search index is already created for a given collection.

        Args:
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
        index_name (str): The name of the Atlas Search index to check.

        Returns:
        bool: True if the index exists, False otherwise.
        """
        url = f"{self.base_url}/groups/{self.group_id}/clusters/{self.cluster_name}/fts/indexes/{db_name}/{collection_name}"
        response = requests.get(url, auth=self.auth)

        if response.status_code == 200:
            indexes = response.json()
            for index in indexes:
                if index.get("name") == index_name:
                    return True
            return False
        else:
            logger.error(f"Failed to retrieve index information. Status Code: {response.status_code}")
            return False
