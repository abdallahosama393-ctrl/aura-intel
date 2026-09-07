import requests

# التوكن الخاص ببوت Aura Intel
TELEGRAM_BOT_TOKEN = "8887889302:AAEDBq3g56UqDiXvjhYnqQaeWmGUlcYrbBQ"

# الـ Chat ID الخاص بك
CHAT_ID = "7602262082"

def send_telegram_alert(product: str, city: str, gap_score: int, price: float):
    """إرسال تنبيه فوري بفجوة تسعيرية جديدة عبر تليجرام"""
    message = (
        f"🚨 *تنبيه فجوة تسعيرية جديدة!* 🚨\n\n"
        f"📦 المنتج: {product}\n"
        f"📍 المدينة: {city}\n"
        f"⭐ درجة الفرصة: {gap_score}/100\n"
        f"💰 السعر المقترح: Rp {price:,.0f}\n\n"
        f"تم رصد هذه الفجوة بواسطة منصة Aura Intel الآلية."
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending telegram message: {e}")
        return None