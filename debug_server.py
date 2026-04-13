import uvicorn
from api import app
import threading
import time
import requests

def start_server():
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='error')

def test_api():
    time.sleep(2)  # Wait for server to start
    try:
        response = requests.post('http://127.0.0.1:8000/chatbot', json={'message': 'test'}, timeout=5)
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    test_api()