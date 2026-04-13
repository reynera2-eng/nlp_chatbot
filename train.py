import json
import pickle
import re
import random

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score

# 🔥 NLP INDONESIA
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# 🔹 Init NLP tools
stem_factory = StemmerFactory()
stemmer = stem_factory.create_stemmer()

stop_factory = StopWordRemoverFactory()
stopword = stop_factory.create_stop_word_remover()

# 🔹 Clean text (WAJIB sama dengan API)
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = stemmer.stem(text)       # 🔥 stemming
    text = stopword.remove(text)    # 🔥 remove kata tidak penting
    return text

# 🔹 Load data
with open("data/intents.json", "r", encoding="utf-8") as f:
    intents = json.load(f)

texts, labels = [], []

for intent, examples in intents.items():
    for text in examples:
        texts.append(clean_text(text))
        labels.append(intent)

# 🔹 Shuffle data
combined = list(zip(texts, labels))
random.shuffle(combined)
texts, labels = zip(*combined)

# 🔹 Split data
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, random_state=42
)

# 🔹 Vectorizer (🔥 UPGRADE)
vectorizer = TfidfVectorizer(ngram_range=(1,2))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# 🔹 Model
model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)

# 🔹 Cross Validation
scores = cross_val_score(model, X_train_vec, y_train, cv=5)
print("Cross-validation accuracy:", scores.mean())

# 🔹 Evaluasi
y_pred = model.predict(X_test_vec)
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy model: {accuracy:.2f}")

# 🔹 Save model
with open("model/chatbot_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("model/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("Model training selesai & tersimpan.")