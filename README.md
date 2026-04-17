# 🤖 Becks Apparel NLP Chatbot

Chatbot berbasis Natural Language Processing (NLP) Bahasa Indonesia yang dikembangkan untuk membantu pelanggan Becks Apparel dalam mendapatkan informasi secara otomatis dan interaktif.

---

## 🚀 Fitur Utama

* ✅ Cek status pesanan (berdasarkan nomor invoice)
* ✅ Informasi cara pemesanan jersey
* ✅ Informasi pembayaran & pengiriman
* ✅ Bantuan penggunaan Jersey Customizer:

  * 🎨 Pengaturan warna jersey
  * 🧩 Motif & pattern
  * 🔤 Nama & nomor punggung
  * 🖼 Upload logo
  * 🔄 Undo / Redo
  * 🌗 Dark mode interface
* ✅ Multi-step conversation (contoh: cek status → input invoice)

---

## 🧠 Teknologi yang Digunakan

* **FastAPI** → Backend API
* **Scikit-learn** → Machine Learning model
* **Sastrawi** → NLP Bahasa Indonesia (stemming & stopword removal)
* **Pickle** → Model serialization
* **HTML + JavaScript** → Chat UI sederhana

---

## 📁 Struktur Project

```
nlp_chatbot/
│
├── api.py                # API utama chatbot (FastAPI)
├── train.py              # Training model NLP
├── model/                # File model & vectorizer
├── data/                 # Dataset intents
├── tests/
│   └── test_chat_ui.html # UI chatbot sederhana untuk testing
├── requirements.txt      # Dependency Python
```

---

## ⚙️ Cara Menjalankan Project

### 1. Clone Repository

```
git clone https://github.com/USERNAME/nlp_chatbot.git
cd nlp_chatbot
```

---

### 2. Aktifkan Virtual Environment

```
.venv\Scripts\activate
```

---

### 3. Install Dependency

```
pip install -r requirements.txt
```

---

### 4. Jalankan Server Chatbot

```
uvicorn api:app --reload
```

Server akan berjalan di:

```
http://127.0.0.1:8000
```

---

### 5. Test API (Swagger UI)

Buka di browser:

```
http://localhost:8000/docs
```

---

## 🧪 Testing UI

Gunakan file:
tests/test_chat_ui.html

Untuk mencoba chatbot secara langsung tanpa integrasi frontend.

---

## 📌 Endpoint API

### POST `/chatbot`

Request:

```json
{
  "message": "cara pesan jersey"
}
```

Response:

```json
{
  "status": "success",
  "intent": "cara_pesan",
  "message": "Anda dapat memesan jersey melalui menu Custom Jersey."
}
```

---

## 🔄 Contoh Interaksi

User:

```
cek status pesanan saya
```

Bot:

```
Silakan masukkan nomor invoice Anda.
```

User:

```
INV001
```

Bot:

```
Status pesanan INV001: Sedang diproduksi
```

---

## 📊 Catatan

* Model menggunakan pendekatan Machine Learning (klasifikasi intent)
* Threshold confidence digunakan untuk fallback response
* Sistem mendukung preprocessing Bahasa Indonesia (stemming & stopword removal)

---

## 👨‍💻 Author

**Alfred Reyner Albiando**
Teknik Informatika - Universitas Pamulang

---

## 📌 Tujuan Project

Project ini dikembangkan sebagai bagian dari:

* Project Work / Skripsi
* Implementasi NLP dalam sistem e-commerce
* Peningkatan layanan customer support otomatis

---

## 🔥 Future Development

* 💬 Integrasi ke website e-commerce (Laravel)
* 📱 UI chatbot modern (floating chat widget)
* 🤖 Integrasi AI lebih advanced (LLM / OpenAI)
* 📦 Deployment ke server/cloud

---
