import json
import requests
import time
import random

class DifyHelper:
    def __init__(self, workflow_api_url:str, workflow_api_key:str, max_retries=5, base_delay=10, max_delay=600):
        """
        Initialize the DifyHelper with retry parameters.
        
        Args:
            workflow_api_url: The URL for the workflow API
            workflow_api_key: The API key for authentication
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Initial delay in seconds (default: 1)
            max_delay: Maximum delay in seconds (default: 60)
        """
        self.workflow_api_url = workflow_api_url
        self.workflow_api_key = workflow_api_key
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def invoke_workflow(self, record: dict)-> dict:
        """
        Invoke the workflow with retry mechanism and exponential backoff.
        
        Args:
            record: The input data for the workflow
            
        Returns:
            The workflow output or an empty dict if all retries fail
        """
        headers = {
            "Authorization": f"Bearer {self.workflow_api_key}", 
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": record,
            "response_mode": "blocking",
            "user": "synthesizer"
        }
        
        retry_count = 0
        while True:
            try:
                response = requests.post(self.workflow_api_url, headers=headers, data=json.dumps(payload))
                response.raise_for_status()  # Raise an exception for 4XX/5XX responses
                
                result = response.json()
                return result["data"].get("outputs", {})
                
            except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    print(f"Failed after {self.max_retries} retries. Last exception: {e}")
                    if 'response' in locals():
                        print(f"Last response: \n{response.text if hasattr(response, 'text') else response}")
                    return {}
                
                # Calculate delay with exponential backoff and jitter
                delay = min(self.max_delay, self.base_delay * (2 ** (retry_count - 1)))
                # Add jitter to avoid thundering herd problem
                jitter = random.uniform(0, 0.1 * delay)
                sleep_time = delay + jitter
                
                print(f"Retry {retry_count}/{self.max_retries} after {sleep_time:.2f}s. Error: {e}")
                time.sleep(sleep_time)