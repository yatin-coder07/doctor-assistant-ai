"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export function Navbar() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true); // ✅ added
  const router = useRouter();

  useEffect(() => {
    let isMounted = true; // ✅ prevent state update after unmount

    const fetchUser = async () => {
      try {
        const res = await fetch("http://localhost:8000/me", {
          credentials: "include",
        });

        if (!res.ok) throw new Error("Failed to fetch user");

        const data = await res.json();
        console.log(data)

        if (!isMounted) return;

        if (data?.error) {
          setUser(null);
        } else {
          setUser(data);
        }
      } catch (err) {
        console.error("User fetch error:", err);
        if (isMounted) setUser(null);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchUser();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleLogout = async () => {
    try {
      await fetch("http://127.0.0.1:8000/logout", {
        method: "POST",
        credentials: "include",
      });

      setUser(null);
      router.push("/login");
    } catch (err) {
      console.error("Logout error:", err);
    }
  };

  return (
    <header className="fixed top-6 left-1/2 -translate-x-1/2 z-50 px-6 py-3 backdrop-blur-md rounded-lg border border-gray-300 bg-white/80 flex items-center justify-between w-[90%] max-w-screen shadow-lg">

      {/* LOGO */}
      <h1 className="text-black font-bold cursor-pointer"
          onClick={() => router.push("/")}>
        Clinician AI
      </h1>

      {/* RIGHT SIDE */}
      <div className="flex items-center gap-4">

        {loading ? (
          // ✅ prevents flicker
          <div className="text-sm text-gray-500 animate-pulse">
            Loading...
          </div>
        ) : !user ? (
          <button
            onClick={() => router.push("/login")}
            className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-full hover:bg-gray-100 transition"
          >
            Login
          </button>
        ) : (
          <div className="flex items-center gap-3 text-white">

            {/* USER INFO */}
            <div className="flex flex-col bg-blue-600 px-3 py-1 rounded-md leading-tight">
              <span className="font-semibold text-sm">
                {user.name || "User"}
              </span>
              <span className="text-xs opacity-90 capitalize">
                {user.role}
              </span>
            </div>

            {/* LOGOUT */}
            <button
              onClick={handleLogout}
              className="text-red-500 text-xs hover:underline transition"
            >
              Logout
            </button>

          </div>
        )}
      </div>
    </header>
  );
}