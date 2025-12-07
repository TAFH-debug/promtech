import { Sidebar } from "@/components/sidebar";
import { Link } from "@heroui/link";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Dashboard page",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 lg:ml-16">
        {children}
      </div>
    </div>;
}

