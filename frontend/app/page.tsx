"use client";

import { Navbar } from "@/components/Navbar";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const checkUser = async () => {
      try {
        const res = await fetch(" http://127.0.0.1:8000/user", {
          credentials: "include",
        });

        if (!res.ok) {
          router.push("/login");
          return;
        }

        const user = await res.json();

      
        if (!user) {
          router.push("/login");
        }

      
        if (user.role === "patient") {
          router.push("/patient");
        } else if (user.role === "doctor") {
          router.push("/doctor");
        } else {
          router.push("/login");
        }
      } catch (err) {
        console.error(err);
        router.push("/login");
      }
    };

    checkUser();
  }, [router]);

  return (
    <nav>
      <Navbar />
    </nav>
  );
}

