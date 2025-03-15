import requests
import json

url = "https://api.siliconflow.cn/v1/chat/completions"
with open("./config/api.txt", "r") as f:
    lines = f.readlines()
api_key = lines[0]

payload = {
    "model": "deepseek-ai/DeepSeek-V3",
    "messages": [{"role": "user", "content": "你好！"}],
    "stream": False,
    "max_tokens": 512,
    "stop": ["null"],
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "frequency_penalty": 0.5,
    "n": 1,
    "response_format": {"type": "text"},
}
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

response = requests.request("POST", url, json=payload, headers=headers)
response = response.text
response = json.loads(response)

print(response["choices"][0]["message"]["content"])
