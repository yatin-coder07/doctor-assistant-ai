from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

from agent import run_agent
from db import get_cursor, conn
from email_service import send_email
from slack_service import send_slack_message

from datetime import datetime, timedelta
import re


# =========================
# 🚀 APP SETUP
# =========================
app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key",
    session_cookie="session",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# 📅 DATE HELPERS
# =========================
TODAY = lambda: datetime.now().strftime("%Y-%m-%d")
TOMORROW = lambda: (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


# =========================
# 🧹 INPUT NORMALIZER
# =========================
def normalize_input(text: str) -> str:
    text = text.strip()

    text = re.sub(r'\btomorrow\b', TOMORROW(), text, flags=re.I)
    text = re.sub(r'\btoday\b', TODAY(), text, flags=re.I)

    def fix_time(m):
        h = int(m.group(1))
        mer = (m.group(2) or "").lower()

        if mer == "pm" and h != 12:
            h += 12
        if mer == "am" and h == 12:
            h = 0

        return f"{h:02d}:00"

    text = re.sub(r'\b(\d{1,2})\s*(am|pm)\b', fix_time, text, flags=re.I)

    return text


# =========================
# 📥 REQUEST MODEL
# =========================
class ChatRequest(BaseModel):
    user_input: str


# =========================
# 💬 CHAT ENDPOINT (MCP)
# =========================
@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    user = request.session.get("user")

    # 🔐 Auth check
    if not user:
        return {"error": "Not logged in"}

    try:
        cleaned_input = normalize_input(req.user_input)

        result = await run_agent(cleaned_input, user)

        # =====================
        # 🔧 TOOL RESULT
        # =====================
        if result.get("type") == "tool_result":
            data = result.get("result", {})
            tool_name = result.get("tool")

            # 🔔 Slack notification
            if tool_name == "book_appointment":
                try:
                    summary = f"""
🩺 New Appointment Booked

👤 Patient: {data.get('patient')}
📅 Date: {data.get('date')}
⏰ Time: {data.get('slot')}
📝 Symptom: {data.get('symptom')}
"""
                    await send_slack_message(summary)
                except Exception as e:
                    print("Slack error:", e)

                # 📧 Email
                if user.get("email"):
                    try:
                        await send_email(
                            to_email=user["email"],
                            subject="Appointment Confirmed 🩺",
                            body=f"""
Hello {data.get('patient')},

Your appointment is confirmed.

Doctor: {data.get('doctor')}
Date: {data.get('date')}
Time: {data.get('slot')}
Symptom: {data.get('symptom')}

Thanks,
Clinic AI
"""
                        )
                    except Exception as e:
                        print("Email error:", e)

            return {
                "response": data
            }

        # =====================
        # 💬 NORMAL RESPONSE
        # =====================
        return {
            "response": result.get("content", "How can I help you?")
        }

    except Exception as e:
        print("🔥 ERROR:", e)
        return {"response": "⚠️ Something went wrong"}


# =========================
# 🔐 LOGIN
# =========================
class LoginRequest(BaseModel):
    name: str
    email: str
    role: str = "patient"


@app.post("/login")
def login(request: LoginRequest, req: Request):
    cur = get_cursor()

    cur.execute("SELECT role, email FROM users WHERE name=%s", (request.name,))
    user = cur.fetchone()

    if user:
        role = user[0]

        if not user[1]:
            cur.execute(
                "UPDATE users SET email=%s WHERE name=%s",
                (request.email, request.name),
            )
            conn.commit()
    else:
        cur.execute(
            "INSERT INTO users (name, email, role) VALUES (%s,%s,%s)",
            (request.name, request.email, request.role),
        )
        conn.commit()
        role = request.role

    cur.close()

    req.session["user"] = {
        "name": request.name,
        "role": role,
        "email": request.email,
    }

    return {"name": request.name, "role": role}


# =========================
# 👤 GET USER
# =========================
@app.get("/me")
def get_me(req: Request):
    user = req.session.get("user")

    if not user:
        return {"error": "Not logged in"}

    return user


# =========================
# 🚪 LOGOUT
# =========================
@app.post("/logout")
def logout(req: Request):
    req.session.clear()
    return {"message": "Logged out"}