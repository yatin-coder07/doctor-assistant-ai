from fastmcp import Client
from llm_client import client as llm
from memory import get_memory, update_memory, clear_memory
import json

MCP_SERVER_URL = "http://localhost:8001/mcp"


async def run_agent(user_input: str, user_context: dict) -> dict:

    if not user_context:
        return {"type": "text", "content": "Not logged in"}

    user_id = user_context.get("name")
    if not user_id:
        return {"type": "text", "content": "Invalid session"}

    role = user_context.get("role", "patient")
    memory = get_memory(user_id)

    # =========================
    # 🔌 MCP — list tools
    # =========================
    try:
        async with Client(MCP_SERVER_URL) as mcp:
            raw_tools = await mcp.list_tools()
    except Exception as e:
        print("🔥 MCP list_tools error:", e)
        return {"type": "text", "content": "Could not reach MCP server."}

    openai_tools = []
    for t in raw_tools:
        schema = t.inputSchema
        if hasattr(schema, "model_json_schema"):
            schema = schema.model_json_schema()

        openai_tools.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": schema
            }
        })

    # =========================
    # 🧠 PROMPT
    # =========================
    role_prompt = (
        "You are an AI clinic assistant helping a patient.\n\n"

        "TOOLS:\n"
        "- check_availability → ONLY for checking slots\n"
        "- book_appointment → ONLY for booking\n\n"

        "STRICT RULES:\n"
        "1. If user asks for slots → use check_availability\n"
        "2. If user wants to book → use book_appointment\n"
        "3. If date + slot + symptom exist → MUST call book_appointment\n"
        "4. NEVER call check_availability if booking intent exists\n"
        "5. DO NOT repeat tool calls unnecessarily\n"
        "6. If a tool returns an error → FIX arguments and retry\n"
    )

    messages = [
        {
            "role": "system",
            "content": role_prompt
        },
        {
            "role": "system",
            "content": (
                f"MEMORY:\n"
                f"date={memory.get('date')}\n"
                f"slot={memory.get('slot')}\n"
                f"symptom={memory.get('symptom')}\n\n"
                f"If all exist → call book_appointment immediately."
            )
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    # =========================
    # 🤖 LLM
    # =========================
    try:
        response = llm.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )
        msg = response.choices[0].message
    except Exception as e:
        print("🔥 LLM error:", e)
        return {"type": "text", "content": "AI error"}

    # =========================
    # 💬 TEXT
    # =========================
    if not msg.tool_calls:
        return {"type": "text", "content": msg.content or "OK"}

    call = msg.tool_calls[0]
    tool_name = call.function.name

    try:
        args = json.loads(call.function.arguments or "{}")
    except:
        args = {}

    # =========================
    # 🧼 ARGUMENT SANITIZATION (ADDED)
    # =========================
    TOOL_ALLOWED_ARGS = {
        "check_availability": ["date", "doctor"],
        "book_appointment": ["date", "slot", "symptom", "doctor", "patient", "email"],
        "get_appointments": ["doctor", "date", "symptom", "patient"]
    }

    allowed = TOOL_ALLOWED_ARGS.get(tool_name, [])
    args = {k: v for k, v in args.items() if k in allowed}

    # normalize slot like "12" → "12:00"
    if "slot" in args:
        if args["slot"] and ":" not in args["slot"]:
            args["slot"] = f"{args['slot']}:00"

    # =========================
    # 🧠 MEMORY MERGE (CRITICAL FIX)
    # =========================
    if role == "patient":
        update_memory(user_id, args)
        memory = get_memory(user_id)

        for key in ["date", "slot", "symptom"]:
            if not args.get(key) and memory.get(key):
                args[key] = memory[key]

    # =========================
    # 👤 CONTEXT
    # =========================
    if tool_name == "book_appointment":
        args["patient"] = user_context["name"]
        args["email"] = user_context.get("email", "")

    # =========================
    # 🔥 CALL MCP
    # =========================
    try:
        async with Client(MCP_SERVER_URL) as mcp:
            result = await mcp.call_tool(tool_name, args)
    except Exception as e:
        print("🔥 MCP error:", e)
        return {"type": "text", "content": "Tool failed"}

    # =========================
    # 📦 PARSE
    # =========================
    data = {}
    try:
        if hasattr(result, "content"):
            for b in result.content:
                if hasattr(b, "text"):
                    try:
                        data = json.loads(b.text)
                    except:
                        data = {"message": b.text}
                    break
        else:
            data = result
    except:
        data = {"message": str(result)}

    if tool_name == "book_appointment" and data.get("status") == "confirmed":
        clear_memory(user_id)

    return {
        "type": "tool_result",
        "tool": tool_name,
        "result": data
    }