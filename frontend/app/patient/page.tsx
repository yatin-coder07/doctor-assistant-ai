// app/patient/page.tsx

import { Navbar } from "@/components/Navbar";
import DashboardLayout from "@/components/dashboard-layout";

export default function PatientPage() {
  return (
    <>
    <nav>
      <Navbar />
    </nav>
    <div className="mt-25">
      
      <DashboardLayout role="patient" />
    </div>
    </>
  );
}