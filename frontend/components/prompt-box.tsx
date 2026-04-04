"use client";

import { useState, useEffect, useRef } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ArrowUpIcon } from "lucide-react";

interface Props {
  role?: "doctor" | "patient";
}

// =========================
// 📦 FORMAT TOOL RESPONSES
// =========================
function formatResponse(content: unknown): string {
  if (typeof content === "string") return content;
  if (!content || typeof content !== "object") return String(content);

  const data = content as Record<string, unknown>;

  // ✅ check_availability
  if ("available_slots" in data) {
    const slots = data.available_slots as string[];
    return slots.length > 0
      ? `Available slots on ${data.date}:\n${slots.map(s => `• ${s}`).join("\n")}`
      : `No slots available on ${data.date}.`;
  }

  // ✅ book_appointment confirmed
  if (data.status === "confirmed") {
    return `✅ Appointment confirmed!\n\n👨‍⚕️ Doctor: ${data.doctor}\n📅 Date: ${data.date}\n⏰ Time: ${data.slot}\n🤒 Symptom: ${data.symptom}`;
  }

  // ✅ booking error (slot taken)
  if ("error" in data) {
    const slots = (data.available_slots as string[]) ?? [];
    return `❌ ${data.error}\n\nAvailable slots:\n${slots.map(s => `• ${s}`).join("\n")}`;
  }
  // ✅ get_appointments (doctor view)
if ("appointments" in data && "total" in data) {
  const appts = data.appointments as Array<Record<string, string>>;
  const filters = data.filters as Record<string, string>;

  const activeFilters = Object.entries(filters)
    .filter(([, v]) => v)
    .map(([k, v]) => `${k}: ${v}`)
    .join(", ");

  if (appts.length === 0) {
    return `No appointments found${activeFilters ? ` for ${activeFilters}` : ""}.`;
  }

  return (
    `📋 ${data.total} appointment(s)${activeFilters ? ` — ${activeFilters}` : ""}:\n\n` +
    appts.map(a =>
      `👤 ${a.patient}\n📅 ${a.date} at ${a.slot}\n🤒 ${a.symptom}\n📌 ${a.status}`
    ).join("\n\n")
  );
}

  // ✅ list_appointments
  if ("appointments" in data) {
    const appts = data.appointments as Array<Record<string, string>>;
    if (appts.length === 0) return "You have no upcoming appointments.";
    return `Your appointments:\n\n${appts
      .map(a => `📅 ${a.date} at ${a.slot}\n   👨‍⚕️ ${a.doctor} — ${a.symptom}`)
      .join("\n\n")}`;
  }

  // fallback
  return JSON.stringify(data, null, 2);


}

export default function RuixenMoonChat({ role = "patient" }: Props) {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatRef.current?.scrollTo({
      top: chatRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMsg = message;
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setMessage("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ user_input: userMsg }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response },
      ]);
    } catch (err) {
      console.log(err);
    }

    setLoading(false);
  };

  const handleKeyDown = (e: any) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const title = role === "doctor" ? "Doctor Assistant AI" : "Clinician AI";
  const subtitle =
    role === "doctor"
      ? "Manage patients, appointments, and schedules efficiently."
      : "Book, check & manage your appointments instantly.";
  const placeholder =
    role === "doctor"
      ? "Ask about patients, schedules..."
      : "Describe symptoms or book appointment...";

  return (
    <div className="flex flex-col h-full w-full">

      {/* Chat Area */}
      <div
        ref={chatRef}
        className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4"
      >
        {messages.length === 0 && (
          <div className="text-center mt-10">
            <h1 className="text-2xl font-bold text-[#004253]">{title}</h1>
            <p className="text-[#50686e] mt-1 text-sm">{subtitle}</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-[#004253] text-white rounded-tr-none"
                  : "bg-[#eceeee] text-[#191c1d] rounded-tl-none"
              }`}
            >
              {/* ✅ THE FIX — always render a string */}
              {formatResponse(msg.content)}
            </div>
          </div>
        ))}

        {loading && (
          <div className="text-sm text-[#50686e] animate-pulse">Thinking...</div>
        )}
      </div>

      {/* Input Box */}
      <div className="p-3 border-t border-[#e1e3e3] bg-white">
        <div className="flex items-end gap-2 bg-[#f2f4f4] rounded-xl p-2">
          <Textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="bg-transparent border-none text-[#191c1d] resize-none focus:ring-0"
          />
          <Button
            onClick={sendMessage}
            className="bg-[#004253] text-white rounded-lg px-3 py-2 hover:bg-[#005b71]"
          >
            <ArrowUpIcon className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}