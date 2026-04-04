"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Login() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState(""); 
  const [role, setRole] = useState("patient");
  const [error, setError] = useState("");
  const router = useRouter();

const handleLogin = async (e: any) => {
  e.preventDefault();

  try {
    const res = await fetch("http://localhost:8000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ name, role, email }), 
    });

    const data = await res.json();

    if (data?.error) {
      setError("Login failed");
      return;
    }

    alert("Login successful 🎉");

    if (data.role === "patient") {
      router.push("/patient");
    } else {
      router.push("/doctor");
    }

  } catch {
    setError("Login failed");
  }
};

  return (
    <main className="min-h-screen flex flex-col md:flex-row bg-[#f8fafa] font-[Inter]">


      <section className="hidden md:flex md:w-1/2 lg:w-3/5 relative overflow-hidden bg-[#004253]">

        <div className="relative z-10 p-16 flex flex-col justify-between w-full text-white">

          <h1 className="text-4xl font-extrabold tracking-tight text-[#8dd0e9]">
            Clinician AI
          </h1>

          <div className="max-w-xl">
            <h2 className="text-5xl font-bold leading-tight mb-6">
              Precision Medicine <br /> Meet Ambient Intelligence.
            </h2>

            <p className="text-lg opacity-90 text-[#cde7ee]">
              Join the future of healthcare. Experience an AI-integrated ecosystem.
            </p>
          </div>

          <div className="flex gap-4">
            <div className="w-12 h-1 bg-[#57fbdb] rounded-full"></div>
            <div className="w-12 h-1 bg-white/20 rounded-full"></div>
            <div className="w-12 h-1 bg-white/20 rounded-full"></div>
          </div>
        </div>

        <div className="absolute bottom-16 right-16 bg-white/80 backdrop-blur-xl p-6 rounded-xl shadow-2xl max-w-xs">
          <p className="text-sm text-gray-700">
            "Clinician AI has reduced workload by 40%"
          </p>
        </div>
      </section>

      {/* RIGHT SIDE */}
      <section className="flex-1 flex items-center justify-center p-8 md:p-16">

        <div className="w-full max-w-md">

          <div className="md:hidden mb-12">
            <h1 className="text-3xl font-extrabold text-[#004253]">
              Clinician AI
            </h1>
          </div>

          <header className="mb-10">
            <h2 className="text-3xl font-bold mb-2">
              Welcome Back
            </h2>

            <p className="text-gray-500">
              Please enter your credentials to proceed.
            </p>
          </header>

          <form onSubmit={handleLogin} className="space-y-6">

         
            <div>
              <label className="text-xs font-bold uppercase text-gray-500 ml-1">
                Name
              </label>

              <input
                className="w-full px-4 py-3.5 mt-2 bg-white rounded-lg ring-1 ring-gray-300 focus:ring-2 focus:ring-[#004253]"
                placeholder="Enter your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

        
            <div>
              <label className="text-xs font-bold uppercase text-gray-500 ml-1">
                Email
              </label>

              <input
                type="email"
                className="w-full px-4 py-3.5 mt-2 bg-white rounded-lg ring-1 ring-gray-300 focus:ring-2 focus:ring-[#004253]"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

          
            <div>
              <label className="text-xs font-bold uppercase text-gray-500 ml-1">
                Role
              </label>

              <select
                className="w-full px-4 py-3.5 mt-2 bg-white rounded-lg ring-1 ring-gray-300"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="patient">Patient</option>
                <option value="doctor">Doctor</option>
              </select>
            </div>

           
            <button
              type="submit"
              className="w-full py-4 px-6 rounded-xl bg-gradient-to-br from-[#004253] to-[#005b71] text-white font-bold shadow-lg hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-2"
            >
              Sign In →
            </button>

            {error && <p className="text-red-500">{error}</p>}
          </form>

          <footer className="mt-12 pt-8 border-t text-center text-gray-500">
            New user? Just enter your name — account auto-created.
          </footer>

        </div>
      </section>
    </main>
  );
}