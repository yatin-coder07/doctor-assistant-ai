// app/doctor/page.tsx

import { Navbar } from "@/components/Navbar";
import DashboardLayout from "@/components/dashboard-layout";

export default function DoctorPage() {
  return (
    <>
    <nav>
      <Navbar />
    </nav>
    <div className="mt-25">
      
      <DashboardLayout role="doctor" />
    </div>
    </>

  );
}