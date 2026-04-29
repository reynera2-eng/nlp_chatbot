import re
import os
import pickle
import random
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import json
import subprocess

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

# 🔹 Load Responses from JSON
RESPONSES_PATH = "data/responses.json"
INTENTS_PATH = "data/intents.json"

def load_responses():
    if os.path.exists(RESPONSES_PATH):
        with open(RESPONSES_PATH, "r") as f:
            return json.load(f)
    return {}

def save_responses(data):
    with open(RESPONSES_PATH, "w") as f:
        json.dump(data, f, indent=4)

def load_intents():
    if os.path.exists(INTENTS_PATH):
        with open(INTENTS_PATH, "r") as f:
            return json.load(f)
    return {}

def save_intents(data):
    with open(INTENTS_PATH, "w") as f:
        json.dump(data, f, indent=4)

RESPONSES = load_responses()

# 🔹 Session user
sessions = {}

greeting_keywords = [
    "halo", "hai", "hi", "hello", "hey",
    "pagi", "selamat pagi",
    "siang", "selamat siang",
    "sore", "selamat sore",
    "malam", "selamat malam",
    "permisi", "punten",
    "bro", "sis"
]

islamic_greetings = [
    "assalamualaikum",
    "assalamu'alaikum",
    "assalamu alaikum",
    "asalamualaikum"
]

def get_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Selamat pagi"
    elif 12 <= hour < 15:
        return "Selamat siang"
    elif 15 <= hour < 18:
        return "Selamat sore"
    else:
        return "Selamat malam"

def check_greeting_match(msg_lower):
    for g in islamic_greetings:
        if msg_lower.startswith(g) or msg_lower == g:
            return "islamic"
    for g in greeting_keywords:
        if msg_lower.startswith(g + " ") or msg_lower == g:
            return "general"
    return None

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
    
    # 0. Load & Init State
    if user_id not in sessions or not isinstance(sessions[user_id], dict):
        sessions[user_id] = {"state": "chatbot", "history": [], "greet_count": 0}
        
    state = sessions[user_id]["state"]
    msg_lower = req.message.lower().strip()

    # Handling TIMEOUT (Request dari frontend timer)
    if msg_lower == "_session_timeout_":
        sessions[user_id] = {"state": "chatbot", "history": [], "greet_count": 0}
        return {
            "status": "timeout",
            "message": "Sesi obrolan telah ditutup otomatis karena tidak ada interaksi selama 10 menit. Silakan kirim pesan baru jika Anda masih butuh bantuan."
        }

    # Memory Tracking - Append user message
    sessions[user_id]["history"].append({"role": "user", "message": req.message})
    sessions[user_id]["history"] = sessions[user_id]["history"][-20:]

    def send_response(data):
        sessions[user_id]["history"].append({"role": "bot", "message": data.get("message", "")})
        return data

    # 1. State: Handover Berakhir (Post-Admin)
    # Jika Laravel memanggil API sementara di FastAPI masih 'admin', 
    # berarti admin baru saja menekan 'Akhiri Chat'.
    if state == "admin":
        sessions[user_id]["state"] = "post_admin_offer"
        state = "post_admin_offer"

    # Handling Jawaban untuk "Ada lagi yang bisa kami bantu?"
    if state == "post_admin_offer":
        if msg_lower in ["ya", "yes", "boleh", "ada"]:
            sessions[user_id]["state"] = "chatbot"
            return send_response({
                "status": "success",
                "message": "Apalagi yang dapat kami bantu? 😊"
            })
        elif msg_lower in ["tidak", "no", "enggak", "selesai", "sudah", "cukup"]:
            sessions[user_id]["state"] = "chatbot"
            return send_response({
                "status": "continue",
                "message": "Baik, senang bisa membantu Anda. Jika ada hal lain yang perlu didiskusikan, silakan tanyakan kembali. Selamat beraktivitas! 😊"
            })
        else:
            # Fluid: Jika user langsung tanya hal lain (cek status, dll), 
            # pindahkan state ke chatbot dan biarkan logika NLP di bawah yang menangani.
            sessions[user_id]["state"] = "chatbot"
            state = "chatbot"

    # 2. Behavior Setelah Handover (Admin Mode) - AI tidak intervensi, biarkan Laravel yang menangani
    if state == "admin":
        return {
            "status": "admin_mode",
            "message": "" # Kosongkan agar tidak ada balasan dummy
        }

    # 2.5 Intercept Global Exit Keywords (Mencegah Loop Fallback)
    exit_keywords = ["selesai", "cukup", "sudah", "tidak ada", "tidak jadi", "terima kasih", "makasih", "thanks", "tutup"]
    if any(key in msg_lower for key in exit_keywords) and len(msg_lower.split()) <= 3:
        sessions[user_id]["state"] = "chatbot"
        return send_response({
            "status": "continue",
            "message": "Baik, terima kasih! 😊 Senang bisa membantu Anda. Jika butuh bantuan lagi di lain waktu, silakan hubungi asisten Becks kembali. Selamat beraktivitas!"
        })

    # 3. Prioritas Greeting
    greet_type = check_greeting_match(msg_lower)
    if greet_type:
        sessions[user_id]["greet_count"] = sessions[user_id].get("greet_count", 0) + 1
        
        # Penanganan SPAM Greeting
        if sessions[user_id]["greet_count"] > 1:
            return send_response({
                "status": "success",
                "intent": "greeting",
                "confidence": 1.0,
                "message": "Halo! 😊 Langsung saja ketikkan pertanyaan atau hal yang ingin Anda diskusikan ya."
            })
            
        # Greeting Normal
        if greet_type == "islamic":
            curr_time_greeting = get_greeting()
            resp_choices = [
                f"Waalaikumsalam, {curr_time_greeting}! 😊 Apa yang bisa saya bantu?",
                f"Waalaikumsalam 🙏 {curr_time_greeting}! Ada yang bisa saya bantu?",
                f"Waalaikumsalam 😊 {curr_time_greeting}! Silakan, ada yang ingin ditanyakan?"
            ]
            return send_response({
                "status": "success",
                "intent": "greeting",
                "confidence": 1.0,
                "message": random.choice(resp_choices)
            })
        elif greet_type == "general":
            curr_time_greeting = get_greeting()
            return send_response({
                "status": "success",
                "intent": "greeting",
                "confidence": 1.0,
                "message": f"{curr_time_greeting}! 😊 Apa yang bisa saya bantu?"
            })
    else:
        # Reset greet_count jika user tanya hal lain
        sessions[user_id]["greet_count"] = 0

    # 3. Prioritas 3 (Part C): Handling Jawaban User (State offer_admin)
    if state == "offer_admin":
        if msg_lower == "ya":
            sessions[user_id]["state"] = "admin"
            return send_response({
                "status": "handover",
                "message": "Anda sekarang terhubung dengan admin.",
                "handover": True
            })
        elif msg_lower == "tidak":
            sessions[user_id]["state"] = "chatbot"
            return send_response({
                "status": "continue",
                "message": "Baik, silakan tanyakan hal lain 😊"
            })
        else:
            # Fluid: Jika bukan ya/tidak, anggap kembali ke chatbot dan lanjut ke logika berikutnya
            sessions[user_id]["state"] = "chatbot"

    # 4. Clean Text
    cleaned_text = clean_text(req.message)
    
    # 5. Vectorize
    vec_text = vectorizer.transform([cleaned_text])
    
    # 6. Predict Intent & Confidence
    probs = ml_model.predict_proba(vec_text)[0]
    max_prob = max(probs)
    intent = ml_model.predict(vec_text)[0]

    # Manual Override: Cek kata kunci handover secara eksplisit
    handover_keywords = ["admin", "bicara admin", "hubungi admin", "panggil admin", "bantuan manusia"]
    if any(k in msg_lower for k in handover_keywords):
        sessions[user_id]["state"] = "offer_admin"
        return send_response({
            "status": "fallback",
            "message": "Apakah Anda ingin terhubung dengan admin untuk bantuan lebih lanjut?",
            "options": ["Ya", "Tidak"]
        })
    
    # 7. Fallback threshold (Disesuaikan kembali ke 0.15 agar intent normal terdeteksi)
    if max_prob < 0.15:
        sessions[user_id]["state"] = "offer_admin"
        return send_response({
            "status": "fallback",
            "intent": "unknown",
            "confidence": round(float(max_prob), 2),
            "message": "Maaf saya belum memahami pertanyaan Anda sepenuhnya. Apakah Anda ingin terhubung dengan admin?",
            "options": ["Ya", "Tidak"]
        })

    # Prioritas 5: NLP Intent
    return send_response({
        "status": "success",
        "intent": str(intent),
        "confidence": round(float(max_prob), 2),
        "message": RESPONSES.get(str(intent), "Silakan hubungi admin.")
    })

# --- ADMIN ENDPOINTS ---

class IntentUpdate(BaseModel):
    intent: str
    response: str
    patterns: list[str]

@app.get("/admin/intents")
def get_all_intents():
    intents = load_intents()
    responses = load_responses()
    combined = []
    for intent, patterns in intents.items():
        combined.append({
            "intent": intent,
            "patterns": patterns,
            "response": responses.get(intent, "")
        })
    return combined

@app.post("/admin/intents")
def update_intent(data: IntentUpdate):
    intents = load_intents()
    responses = load_responses()
    
    intents[data.intent] = data.patterns
    responses[data.intent] = data.response
    
    save_intents(intents)
    save_responses(responses)
    
    # Reload local cache
    global RESPONSES
    RESPONSES = responses
    
    return {"status": "success", "message": f"Intent {data.intent} updated."}

@app.delete("/admin/intents/{intent}")
def delete_intent(intent: str):
    intents = load_intents()
    responses = load_responses()
    
    if intent in intents: del intents[intent]
    if intent in responses: del responses[intent]
    
    save_intents(intents)
    save_responses(responses)
    
    global RESPONSES
    RESPONSES = responses
    
    return {"status": "success", "message": f"Intent {intent} deleted."}

@app.post("/admin/retrain")
def retrain_model():
    try:
        # Menjalankan train.py
        result = subprocess.run(["python", "train.py"], capture_output=True, text=True)
        if result.returncode == 0:
            # Reload model
            global ml_model, vectorizer
            if os.path.exists(MODEL_PATH) and os.path.exists(VEC_PATH):
                with open(MODEL_PATH, "rb") as f:
                    ml_model = pickle.load(f)
                with open(VEC_PATH, "rb") as f:
                    vectorizer = pickle.load(f)
            return {"status": "success", "message": "Model retrained successfully."}
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}
