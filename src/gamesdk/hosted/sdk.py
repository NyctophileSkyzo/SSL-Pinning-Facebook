import requests


class GameSDK:
    api_url: str = "https://game-api.virtuals.io/api"
    api_key: str

    def __init__(self, api_key: str):
        self.api_key = api_key

    def functions(self):
        """
        Get all default functions
        """
        response = requests.get(
            f"{self.api_url}/functions", headers={"x-api-key": self.api_key})

        if (response.status_code != 200):
            raise Exception(response.json())

        functions = {}

        for x in response.json()["data"]:
            functions[x["fn_name"]] = x["fn_description"]

        return functions

    def simulate(self, session_id: str,  goal: str, description: str, world_info: str, functions: list, custom_functions: list):
        """
        Simulate the agent configuration
        """
        response = requests.post(
            f"{self.api_url}/simulate",
            json={
                "data": {
                    "sessionId": session_id,
                    "goal": goal,
                    "description": description,
                    "worldInfo": world_info,
                    "functions": functions,
                    "customFunctions": [x.toJson() for x in custom_functions]
                }
            },
            headers={"x-api-key": self.api_key}
        )

        if (response.status_code != 200):
            raise Exception(response.json())

        return response.json()["data"]

    def react(self, session_id: str, platform: str, goal: str,
              description: str, world_info: str, functions: list, custom_functions: list,
              event: str = None, task: str = None, tweet_id: str = None):
        """
        Simulate the agent configuration
        """
        url = f"{self.api_url}/react/{platform}"

        payload = {
            "sessionId": session_id,
            "goal": goal,
            "description": description,
            "worldInfo": world_info,
            "functions": functions,
            "customFunctions": [x.toJson() for x in custom_functions]
        }

        if (event):
            payload["event"] = event

        if (task):
            payload["task"] = task
            
        if (tweet_id):
            payload["tweetId"] = tweet_id
            
        print(payload)

        response = requests.post(
            url,
            json={
                "data": payload
            },
            headers={"x-api-key": self.api_key}
        )

        if (response.status_code != 200):
            raise Exception(response.json())

        return response.json()["data"]

    def deploy(self, goal: str, description: str, world_info: str, functions: list, custom_functions: list, main_heartbeat: int, reaction_heartbeat: int, tweet_usernames: list = None, templates: list = None, game_engine_model: str = "llama_3_1_405b"):
        """
        Simulate the agent configuration
        """
        payload = {
            "goal": goal,
            "description": description,
            "worldInfo": world_info,
            "functions": functions,
            "customFunctions": [x.toJson() for x in custom_functions],
            "gameState": {
                "mainHeartbeat": main_heartbeat,
                "reactionHeartbeat": reaction_heartbeat,
            },
            "gameEngineModel": game_engine_model
        }
            
        if tweet_usernames is not None:
            payload["tweetUsernames"] = tweet_usernames
            
        # Add templates to payload if provided
        if templates:
            payload["templates"] = [template.to_dict() for template in templates]   
            
        response = requests.post(
            f"{self.api_url}/deploy",
            json={
                "data": payload
            },
            headers={"x-api-key": self.api_key}
        )

        if (response.status_code != 200):
            raise Exception(response.json())

        return response.json()["data"]
    
    def reset_memory(self):
        response = requests.get(
            f"{self.api_url}/reset-session", headers={"x-api-key": self.api_key})

        if (response.status_code != 200):
            raise Exception("Failed to reset memory.")

        return "Memory reset successfully."
