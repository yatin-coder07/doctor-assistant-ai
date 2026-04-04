"use client";

import RuixenMoonChat from "@/components/prompt-box";

export default function DashboardLayout({ role }: { role: "doctor" | "patient" }) {
  return (
    <div className="bg-[#eef2f3] min-h-screen w-full px-6 py-8"> {/* 🔥 softer gray bg */}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* LEFT PANEL */}
        <div className="lg:col-span-4 space-y-6">

          {/* 🔥 PRIMARY BLUE CARD */}
          <div className="bg-[#004253] text-white rounded-2xl p-6 shadow-lg">
            <h2 className="text-xl font-bold mb-2">
              AI Assistant
            </h2>

            <p className="text-sm text-white/80 leading-relaxed">
              This assistant uses <span className="font-semibold text-white">MCP</span> 
              to intelligently understand your intent.
            </p>

            <ul className="mt-4 space-y-2 text-sm text-white/90">
              <li>⚡ Checks doctor availability instantly</li>
              <li>📅 Books appointments automatically</li>
              <li>🧠 Asks for missing medical details</li>
              <li>🔄 Maintains conversation context</li>
            </ul>
          </div>

          {/* WHITE CARD */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#e1e3e3]">
            <h3 className="font-bold text-[#004253] mb-3">
              {role === "doctor" ? "Doctor Tools" : "Patient Support"}
            </h3>

            <p className="text-sm text-[#50686e]">
              {role === "doctor"
                ? "View schedules, manage patient bookings, and track appointments efficiently."
                : "Describe symptoms, check availability, and get booked instantly without hassle."}
            </p>
          </div>

          {/* LIGHT GRAY CARD */}
          <div className="bg-[#e6e8e8] rounded-2xl p-6">
            <h4 className="font-semibold text-[#191c1d] mb-2">
              Smart System
            </h4>
            <p className="text-xs text-[#50686e]">
              No manual forms. The AI dynamically collects only required fields before booking.
            </p>
          </div>

        </div>

        {/* RIGHT PANEL */}
        <div className="lg:col-span-8 flex flex-col gap-6">

          {/* CHAT BOX */}
          <div className="bg-white rounded-2xl shadow-xl border border-[#e1e3e3] overflow-hidden h-[500px]">
            <RuixenMoonChat role={role} />
          </div>

          {/* BOTTOM CARDS */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

            {/* NORMAL CARD */}
            <div className="bg-white p-6 rounded-2xl border border-[#e1e3e3]">
              <h4 className="font-bold text-[#004253]">Automation</h4>
              <p className="text-sm text-[#50686e] mt-2">
                The system automatically selects the best available slot based on real-time availability.
              </p>
            </div>

            {/* 🔥 ACCENT CARD */}
            <div className="bg-[#004253] text-white p-6 rounded-2xl shadow-lg">
              <h4 className="font-bold">Accuracy</h4>
              <p className="text-sm text-white/80 mt-2">
                Uses structured MCP prompts instead of if-else logic for reliable responses.
              </p>
            </div>

          </div>

        </div>
      </div>
    </div>
  );
}