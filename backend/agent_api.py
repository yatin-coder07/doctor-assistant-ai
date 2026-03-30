from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel


import json
import ollama
from datetime import datetime, timedelta
import inspect
import re

from db import conn, get_cursor
from google_calendar import create_event
from email_service import send_email
from slack_service import send_slack_message


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

# Per-user booking memory: { username -> { date, slot, symptom } }
booking_memory: dict[str, dict] = {}

TODAY    = lambda: datetime.now().strftime("%Y-%m-%d")
TOMORROW = lambda: (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")



def check_availability(date: str, doctor: str = "Dr Ahuja") -> dict:
    cur = get_cursor()
    cur.execute(
        "SELECT time_slot FROM appointments WHERE doctor=%s AND date=%s",
        (doctor, date),
    )
    booked = [r[0] for r in cur.fetchall()]
    cur.close()
    available = [s for s in ["10:00", "12:00", "15:00"] if s not in booked]
    return {"doctor": doctor, "date": date, "available_slots": available}


def book_appointment(date: str, slot: str, symptom: str,
                     doctor: str = "Dr Ahuja",
                     patient: str = "Patient",
                     email: str = None) -> dict:

    avail = check_availability(date, doctor)
    if slot not in avail["available_slots"]:
        return {"error": f"Slot {slot} already taken. Available: {avail['available_slots']}"}

    cur = get_cursor()
    cur.execute(
        "INSERT INTO appointments (doctor, patient, email, date, time_slot, symptom, status)"
        " VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (doctor, patient, email, date, slot, symptom, "booked"),
    )
    conn.commit()
    cur.close()

    try:
        create_event(date, slot)
    except Exception:
        pass

    return {
        "status": "confirmed",
        "doctor": doctor,
        "patient": patient,
        "email": email,
        "date": date,
        "slot": slot,
        "symptom": symptom,
    }

def get_patients_by_date(date: str) -> dict:
    cur = get_cursor()
    cur.execute(
        "SELECT patient, time_slot, symptom, status FROM appointments"
        " WHERE date=%s ORDER BY time_slot", (date,),
    )
    rows = cur.fetchall()
    cur.close()
    return {"date": date, "count": len(rows),
            "appointments": [{"patient": r[0], "slot": r[1], "symptom": r[2], "status": r[3]} for r in rows]}


def get_patients_by_symptom(symptom: str) -> dict:
    cur = get_cursor()
    cur.execute(
        "SELECT patient, date, time_slot, symptom, status FROM appointments"
        " WHERE LOWER(symptom) LIKE %s ORDER BY date, time_slot",
        (f"%{symptom.lower()}%",),
    )
    rows = cur.fetchall()
    cur.close()
    return {"symptom": symptom, "count": len(rows),
            "appointments": [{"patient": r[0], "date": str(r[1]), "slot": r[2], "symptom": r[3], "status": r[4]} for r in rows]}


def get_all_patients() -> dict:
    cur = get_cursor()
    cur.execute("SELECT patient, date, time_slot, symptom, status FROM appointments ORDER BY date, time_slot")
    rows = cur.fetchall()
    cur.close()
    return {"count": len(rows),
            "appointments": [{"patient": r[0], "date": str(r[1]), "slot": r[2], "symptom": r[3], "status": r[4]} for r in rows]}


def get_summary(period: str = "today") -> dict:
    d = TODAY() if period == "today" else TOMORROW()
    cur = get_cursor()
    cur.execute("SELECT COUNT(*) FROM appointments WHERE date=%s", (d,))
    count = cur.fetchone()[0]
    cur.close()
    return {"period": period, "date": d, "count": count}


TOOLS = {
    "check_availability":      check_availability,
    "book_appointment":        book_appointment,
    "get_patients_by_date":    get_patients_by_date,
    "get_patients_by_symptom": get_patients_by_symptom,
    "get_all_patients":        get_all_patients,
    "get_summary":             get_summary,
}





def filter_args(func, args: dict) -> dict:
    sig = inspect.signature(func)
    return {k: v for k, v in args.items() if k in sig.parameters}


def normalize_input(text: str) -> str:
    text = text.strip()
    text = re.sub(r'!\s*0', '10', text)
    text = re.sub(r'\btomorrow\b', TOMORROW(), text, flags=re.I)
    text = re.sub(r'\btoday\b',    TODAY(),    text, flags=re.I)

    def fix_time(m):
        h = int(m.group(1))
        mer = (m.group(2) or "").lower()
        if mer == "pm" and h != 12: h += 12
        if mer == "am" and h == 12: h = 0
        return f"{h:02d}:00"
    text = re.sub(r'\b(\d{1,2})\s*(am|pm)\b', fix_time, text, flags=re.I)
    text = re.sub(r'(?<!\d)(10|12|15)(?![:0-9])', lambda m: f"{m.group(1)}:00", text)
    return text




def ask_llm(user_input: str, memory_state: dict) -> str:
    memory_str = json.dumps(memory_state) if memory_state else "{}"

    prompt = f"""You are a clinic receptionist AI. You only output JSON. Never output plain text.

TODAY = {TODAY()}
TOMORROW = {TOMORROW()}
VALID SLOTS = 10:00, 12:00, 15:00

=== CURRENT BOOKING MEMORY ===
{memory_str}
(These fields are already known. Never ask for them again.)

=== USER SAID ===
{user_input}

=== YOUR JOB ===
Read the user message. Pick EXACTLY ONE of the JSON outputs below.

--- CASE 1: User asks if doctor is free on a date ---
Output: {{"tool": "check_availability", "args": {{"date": "YYYY-MM-DD"}}}}

--- CASE 2: User wants to book AND date is known in memory OR in message ---
Step A: First call check_availability to get free slots.
Output: {{"tool": "check_availability", "args": {{"date": "YYYY-MM-DD"}}}}
(Backend will then show free slots and ask user to pick slot + symptom together in one message.)

--- CASE 3: User has provided slot AND symptom (both present in message or memory) ---
Output: {{"tool": "book_appointment", "args": {{"date": "YYYY-MM-DD", "slot": "HH:MM", "symptom": "TEXT"}}}}

--- CASE 4: User wants to book but date is NOT known ---
Output: {{"tool": "ask_user", "message": "Which date would you like the appointment?"}}

--- CASE 5: Doctor asks for patients on a date ---
Output: {{"tool": "get_patients_by_date", "args": {{"date": "YYYY-MM-DD"}}}}

--- CASE 6: Doctor asks for patients with a symptom ---
Output: {{"tool": "get_patients_by_symptom", "args": {{"symptom": "TEXT"}}}}

--- CASE 7: Doctor asks for all patients ---
Output: {{"tool": "get_all_patients", "args": {{}}}}

--- CASE 8: Doctor asks how many appointments today or tomorrow ---
Output: {{"tool": "get_summary", "args": {{"period": "today"}}}}
Output: {{"tool": "get_summary", "args": {{"period": "tomorrow"}}}}

=== STRICT RULES ===
- Output ONLY the JSON. No explanation. No extra words. No markdown.
- Never ask for date and slot separately. After check_availability the backend asks for BOTH slot and symptom together.
- Never assume a slot. Never assume a symptom. Only use values the user actually said.
- If date in memory, use it. If slot in memory, use it. If symptom in memory, use it.
- Never give medical advice.

Output JSON now:"""

    res = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0},
    )
    return res["message"]["content"]


def parse_llm(raw: str) -> dict:
    """Robustly extract JSON from LLM output."""
    raw = re.sub(r'```(?:json)?\s*|\s*```', '', raw).strip()
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {"tool": "none"}


def chat_llm(user_input: str) -> str:
    """
    Called when no tool matched — LLM replies conversationally
    as a friendly clinic receptionist.
    """
    res = ollama.chat(
        model="mistral",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a friendly receptionist at Dr Ahuja's clinic. "
                    "Reply in 1-2 short sentences. "
                    "If the user is chatting casually, greet them warmly and let them know "
                    "you can help them book an appointment or answer clinic questions. "
                    "Never give medical advice."
                ),
            },
            {"role": "user", "content": user_input},
        ],
        options={"temperature": 0.4},
    )
    return res["message"]["content"].strip()




class ChatRequest(BaseModel):
    user_input: str

@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    user = request.session.get("user")
    if not user:
        return {"error": "Not logged in"}

    username = user["name"]
    user_email = user.get("email")

    user_input = normalize_input(req.user_input)
    mem = booking_memory.setdefault(username, {})


    try:
        raw = ask_llm(user_input, mem)
        decision = parse_llm(raw)
    except Exception as e:
        print(" LLM ERROR:", e)
        return {
            "response": "⚠️ AI is temporarily down. Please try again."
        }

    tool = decision.get("tool", "none")
    args = decision.get("args", {})


    if tool == "check_availability":
        date = args.get("date")
        if not date:
            return {"response": "Which date would you like to check?"}

        result = check_availability(date)
        slots = result["available_slots"]

        if not slots:
            return {"response": f"No slots available on {date}."}

        mem["date"] = date

        return {
            "response": f"Dr Ahuja is free on {date} at: {', '.join(slots)}. Which slot would you like and what is your symptom?"
        }

 
    if tool == "book_appointment":

        for k, v in args.items():
            if v:
                mem[k] = v

        missing = [f for f in ("date", "slot", "symptom") if not mem.get(f)]

        if missing:
            if missing == ["slot"]:
                avail = check_availability(mem["date"])
                free = avail["available_slots"]

                if not free:
                    booking_memory[username] = {}
                    return {"response": f"No slots available on {mem['date']}. Please choose another date."}

                return {
                    "response": f"Available slots on {mem['date']}: {', '.join(free)}. Which one and what is your symptom?"
                }

            return {"response": f"Please provide: {', '.join(missing)}"}

        avail = check_availability(mem["date"])

        if mem["slot"] not in avail["available_slots"]:
            free = avail["available_slots"]
            mem.pop("slot", None)

            if not free:
                booking_memory[username] = {}
                return {"response": f"No slots available on {mem['date']}. Please choose another date."}

            return {
                "response": f"Slot {mem['slot']} is taken. Free slots: {', '.join(free)}. Which one?"
            }

       
        result = book_appointment(
            date=mem["date"],
            slot=mem["slot"],
            symptom=mem["symptom"],
            patient=username,
            email=user_email,
        )

        booking_memory[username] = {}

        if "error" in result:
            return {"response": result["error"]}


        try:
            summary = f"""
*🩺 New Appointment Booked*

👤 *Patient:* {username}
📅 *Date:* {result['date']}
⏰ *Time:* {result['slot']}
📝 *Symptom:* {result['symptom']}
"""
            await send_slack_message(summary)
            print("✅ Slack notification sent")
        except Exception as e:
            print("❌ Slack failed:", e)


        print("📧 SESSION EMAIL:", user_email)

        if user_email:
            try:
                await send_email(
                    to_email=user_email,
                    subject="Appointment Confirmed 🩺",
                    body=f"""
Hello {username},

Your appointment has been confirmed.

Doctor: {result['doctor']}
Date: {result['date']}
Time: {result['slot']}
Symptom: {result['symptom']}

Thank you,
Clinician AI
""",
                )
                print("✅ Email sent successfully")
            except Exception as e:
                print("❌ Email failed:", e)
        else:
            print("⚠️ No email found in session for user:", username)

        return {
            "response": f"✅ Appointment confirmed with {result['doctor']} on {result['date']} at {result['slot']}. Symptom: {result['symptom']}."
        }


    try:
        return {"response": chat_llm(req.user_input)}
    except Exception as e:
        print("🔥 fallback LLM error:", e)
        return {"response": "Hello! How can I help you today?"}

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

@app.get("/me")
def get_me(req: Request):
    user = req.session.get("user")
    if not user:
        return {"error": "Not logged in"}
    return user


@app.post("/logout")
def logout(req: Request):
    req.session.clear()
    return {"message": "Logged out"}