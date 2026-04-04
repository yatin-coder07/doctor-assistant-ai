import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP
from db import get_cursor, conn
from google_calendar import create_event

mcp = FastMCP("clinic-mcp")

SLOTS = ["10:00", "12:00", "15:00"]



@mcp.tool()
def check_availability(date: str, doctor: str = "Dr Ahuja") -> dict:
    """PATIENT TOOL: Check which time slots are still open for booking on a given date.
        ONLY use this when the user is asking to SEE available slots.

    DO NOT use this if the user is trying to BOOK an appointment.

    Example:
    - "What slots are available tomorrow?" ✅ use this
    - "Book me at 10 tomorrow" ❌ DO NOT use this
"""
    cur = get_cursor()
    cur.execute(
        "SELECT time_slot FROM appointments WHERE doctor=%s AND date=%s",
        (doctor, date),
    )
    booked = [r[0] for r in cur.fetchall()]
    cur.close()
    available = [s for s in SLOTS if s not in booked]
    return {"doctor": doctor, "date": date, "available_slots": available}


@mcp.tool()
def book_appointment(
    date: str,
    slot: str,
    symptom: str,
    doctor: str = "Dr Ahuja",
    patient: str = "",
    email: str = ""
) -> dict:
    """Book a confirmed appointment slot for a patient.
     Use this tool when the user wants to CONFIRM or BOOK an appointment.

    REQUIREMENTS:
    - date must be provided
    - slot must be provided
    - symptom must be provided

    IMPORTANT:
    If all required fields are available, ALWAYS call this tool immediately.
    DO NOT call check_availability first.

    Example:
    - "Book me tomorrow at 10 for fever" ✅ MUST call this"""
    avail = check_availability(date, doctor)
    if slot not in avail["available_slots"]:
        return {
            "error": f"Slot {slot} is no longer available.",
            "available_slots": avail["available_slots"]
        }

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
    except Exception as e:
        print(f"Calendar error (non-fatal): {e}")

    return {
        "status": "confirmed",
        "doctor": doctor,
        "patient": patient,
        "date": date,
        "slot": slot,
        "symptom": symptom
    }


@mcp.tool()
def get_appointments(
    doctor: str = "Dr Ahuja",
    date: str = "",
    symptom: str = "",
    patient: str = ""
) -> dict:
    """DOCTOR TOOL: Fetch and filter patient appointments by date, symptom, or patient name. Use this to view schedules and patient lists."""
    cur = get_cursor()

    query = "SELECT patient, email, date, time_slot, symptom, status FROM appointments WHERE doctor=%s"
    params = [doctor]

    if date:
        query += " AND date=%s"
        params.append(date)

    if symptom:
        query += " AND LOWER(symptom) LIKE %s"
        params.append(f"%{symptom.lower()}%")

    if patient:
        query += " AND LOWER(patient) LIKE %s"
        params.append(f"%{patient.lower()}%")

    query += " ORDER BY date, time_slot"

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()

    return {
        "doctor": doctor,
        "filters": {"date": date, "symptom": symptom, "patient": patient},
        "total": len(rows),
        "appointments": [
            {
                "patient": r[0],
                "email": r[1],
                "date": str(r[2]),
                "slot": r[3],
                "symptom": r[4],
                "status": r[5]
            }
            for r in rows
        ]
    }

if __name__ == "__main__":
    mcp.run(transport="http", port=8001)