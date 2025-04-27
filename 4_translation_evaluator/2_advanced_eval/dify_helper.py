import json
import requests

class DifyHelper:
    def __init__(self, workflow_api_url:str, workflow_api_key:str):
        self.workflow_api_url = workflow_api_url
        self.workflow_api_key = workflow_api_key

    def invoke_workflow(self, record: dict)-> dict:
        try:
            headers = {
                "Authorization": f"Bearer {self.workflow_api_key}", 
                "Content-Type": "application/json"
            }
            payload = {
                "inputs": record,
                "response_mode": "blocking",
                "user": "synthesizer"
            }

            response = requests.post(self.workflow_api_url, headers=headers, data=json.dumps(payload))
            result = response.json()
            return result["data"].get("outputs", {})

        except Exception as e:
            print(f"exception: {e}")