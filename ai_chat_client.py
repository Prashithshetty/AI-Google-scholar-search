import requests
import json

class AIChatClient:
    def __init__(self, api_url="http://localhost:1234/v1/chat/completions", model="qwen2.5-7b-instruct-1m"):
        self.api_url = api_url
        self.model = model

    def chat(self, messages, temperature=0.7, max_tokens=-1, stream=False):
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            # Assuming the response contains choices with message content
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                return None
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
