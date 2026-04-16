import re
import os
import pickle
from fastapi import FastAPI
from pydantic import BaseModel

# 🔹 Load ML Model & Vectorizer
MODEL_PATH = "model/chatbot_model.pkl"
VEC_PATH = "model/vectorizer.pkl"

ml_model = None
vectorizer = None

if os.path.exists(MODEL_PATH) and os.path.exists(VEC_PATH):
    with open(MODEL_PATH, "rb") as f:
        ml_model = pickle.load(f)
    with open(VEC_PATH, "rb") as f:
        vectorizer = pickle.load(f)

# 🔥 NLP INDONESIA (WAJIB SAMA)
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from fastapi.middleware.cors import CORSMiddleware

# Init NLP
stem_factory = StemmerFactory()
stemmer = stem_factory.create_stemmer()

stop_factory = StopWordRemoverFactory()
stopword = stop_factory.create_stop_word_remover()

app = FastAPI(title="Becks Apparel NLP Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"

# 🔹 Response default
RESPONSES = {
    "cek_status": "Silakan masukkan nomor invoice Anda.",
    "cara_pesan": "Anda dapat memesan jersey melalui menu Custom Jersey.",
    "pengiriman": "Estimasi pengiriman adalah 3–5 hari kerja.",
    "pembayaran": "Kami mendukung pembayaran melalui QRIS dan transfer bank.",
    "mockup_jersey": "Jersey Customizer menyediakan pilihan model:​ V-Neck, O-Neck, dan tipe Kombinasi. Setiap model dirancang untuk visual 2.5D yang mendalam.",
    "pewarnaan_jersey": "Anda dapat mengubah warna setiap bagian jersey secara spesifik: badan, lengan kanan, lengan kiri, kerah, sabuk, dan lainnya. Setiap bagian memiliki kontrol warna independen.",
    "motif_pattern": "Motif/Pattern dapat diterapkan dengan kontrol penuh terhadap skala, sudut rotasi, dan pencerminan (flip). Anda bisa mengatur ukuran, memutar, dan merefleksikan motif sesuai kebutuhan.",
    "nama_nomor_logo": "Anda dapat menambahkan Nama dan Nomor punggung dengan warna yang bisa disesuaikan. Logo kustom juga bisa diupload dan diposisikan sesuai keinginan dengan kontrol penuh.",
    "view_tampilan": "Pengaturan desain (warna, motif, dll) dipisahkan secara independen untuk tiga view: Depan, Belakang, dan Celana. Setiap view bisa memiliki desain yang berbeda.",
    "undo_redo": "Jersey Customizer memiliki fitur History System dengan Undo & Redo. Tekan Ctrl+Z untuk membatalkan langkah terakhir dan Ctrl+Shift+Z untuk mengulang.",
    "flip_cermin": "Anda dapat mencerminkan logo atau motif dengan fitur Flip Horizontal/Vertical hanya dengan satu klik untuk kemudahan desain.",
    "toolbar_kontrol": "Interactive Toolbar yang melayang memberikan akses cepat ke fitur duplikasi, hapus, dan flip pada objek yang dipilih.",
    "simpan_Download": "Desain Anda dapat disimpan dan didownload dalam format yang didukung. Hubungi admin untuk informasi format file yang tersedia."
}

# 🔹 Session user
sessions = {}

# 🔹 Dummy database
ORDERS = {
    "INV001": "Sedang diproduksi",
    "INV002": "Quality Control",
    "INV003": "Sudah dikirim",
}

# 🔥 Clean text (HARUS IDENTIK dengan train.py)
def clean_text(text):
    try:
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        text = stemmer.stem(text)
        text = stopword.remove(text)
        return text
    except Exception as e:
        # Fallback if preprocessing fails
        return text.lower()


@app.post("/chatbot")
def chatbot(req: ChatRequest):
    if ml_model is None or vectorizer is None:
        return {
            "status": "error",
            "intent": "unknown",
            "confidence": 0.0,
            "message": "Model Machine Learning belum dilatih. Silakan jalankan train.py."
        }

    user_id = req.user_id
    state = sessions.get(user_id, "chatbot")
    msg_lower = req.message.lower().strip()

    # 1. Reset ke Chatbot
    if msg_lower in ["selesai", "kembali ke bot"]:
        sessions[user_id] = "chatbot"
        return {
            "status": "continue",
            "message": "Anda telah kembali ke bot. Silakan tanyakan hal lain 😊"
        }

    # 2. Behavior Setelah Handover (Admin Mode)
    if state == "admin":
        return {
            "status": "admin_mode",
            "message": "Admin: Terima kasih, kami akan membantu Anda."
        }

    # 3. Handling Jawaban User (State offer_admin)
    if state == "offer_admin":
        if msg_lower == "ya":
            sessions[user_id] = "admin"
            return {
                "status": "handover",
                "message": "Anda sekarang terhubung dengan admin.",
                "handover": True
            }
        elif msg_lower == "tidak":
            sessions[user_id] = "chatbot"
            return {
                "status": "continue",
                "message": "Baik, silakan tanyakan hal lain 😊"
            }
        else:
            return {
                "status": "waiting_confirmation",
                "message": "Silakan jawab 'Ya' atau 'Tidak'."
            }

    # 1. Clean Text
    cleaned_text = clean_text(req.message)
    
    # 2. Vectorize
    vec_text = vectorizer.transform([cleaned_text])
    
    # 3. Predict Intent & Confidence
    probs = ml_model.predict_proba(vec_text)[0]
    max_prob = max(probs)
    intent = ml_model.predict(vec_text)[0]
    
    # 4. Fallback threshold
    if max_prob < 0.12:
        sessions[user_id] = "offer_admin"
        return {
            "status": "fallback",
            "intent": "unknown",
            "confidence": round(float(max_prob), 2),
            "message": "Maaf saya belum memahami pertanyaan Anda. Apakah Anda ingin terhubung dengan admin?",
            "options": ["Ya", "Tidak"]
        }

    return {
        "status": "success",
        "intent": str(intent),
        "confidence": round(float(max_prob), 2),
        "message": RESPONSES.get(str(intent), "Silakan hubungi admin.")
    }