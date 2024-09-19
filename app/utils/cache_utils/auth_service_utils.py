import json

import requests
from flask import current_app, g


class AuthService:
    def __init__(self, auth_token=None):
        self.headers = {"Authorization": "Bearer " + auth_token, "Content-Type": "application/json"}
        self.base_url = current_app.config["AUTH_SERVICE_API"]

    def get_policy_data_from_role(self, role_id):
        url_to_hit = self.base_url + "/v1/roles/" + str(role_id)
        response = requests.get(url_to_hit, headers=self.headers, allow_redirects=False)
        json_response = response.json()
        if json_response.get("success"):
            return json_response["data"]["policies"]
        return False

    def get_user_data_by_id(self, user_id):
        url_to_hit = self.base_url + "/v1/users/" + user_id
        response = requests.get(url_to_hit, headers=self.headers, allow_redirects=False)
        json_response = response.json()
        if json_response.get("success"):
            return json_response["data"]
