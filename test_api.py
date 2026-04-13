import requests

# Test API chatbot
url = "http://127.0.0.1:8000/chatbot"
data = {"message": "apa saja model jersey yang tersedia"}

try:
    response = requests.post(url, json=data, timeout=5)
    print("Status Code:", response.status_code)
    print("Headers:", dict(response.headers))
    if response.status_code == 200:
        print("Response:", response.json())
    else:
        print("Error Response:", response.text)
        print("Response content:", response.content)
except requests.exceptions.RequestException as e:
    print("Request Error:", e)