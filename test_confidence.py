from api import clean_text, model, vectorizer

# Test different messages
test_messages = [
    'apa saja model jersey yang tersedia',
    'cara pesan jersey',
    'cek status pesanan',
    'pembayaran bagaimana',
    'warna jersey bisa diganti',
    'motif apa saja'
]

for msg in test_messages:
    cleaned = clean_text(msg)
    X = vectorizer.transform([cleaned])
    proba = model.predict_proba(X)[0]
    confidence = float(max(proba))
    intent = model.classes_[proba.argmax()]
    print(f'Message: "{msg}"')
    print(f'Intent: {intent}, Confidence: {confidence:.3f}')
    print('---')