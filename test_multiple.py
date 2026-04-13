import requests

test_messages = [
    'apa saja model jersey yang tersedia',
    'bagaimana cara mengubah warna jersey',
    'cara menambahkan motif',
    'bagaimana cara pesan jersey',
    'cek status pesanan'
]

for msg in test_messages:
    try:
        response = requests.post('http://127.0.0.1:8000/chatbot', json={'message': msg}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f'Input: "{msg}"')
            print(f'Intent: {data["intent"]}, Confidence: {data["confidence"]}')
            print('---')
        else:
            print(f'Error for "{msg}": {response.status_code}')
    except Exception as e:
        print(f'Error testing "{msg}": {e}')