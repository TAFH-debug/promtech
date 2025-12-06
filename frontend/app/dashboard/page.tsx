"use client";

import dynamic from "next/dynamic";
import { Sidebar } from "@/components/sidebar";
import { Card, CardBody, CardHeader } from "@heroui/card";
import {
  MapPin,
} from "lucide-react";

const MapDraw = dynamic(() => import("@/components/map-draw").then((mod) => ({ default: mod.MapDraw })), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-[600px] text-default-400">
      <div className="text-center">
        <MapPin className="h-12 w-12 mx-auto mb-2 opacity-50" />
        <p>Загрузка карты...</p>
      </div>
    </div>
  ),
});

export default function DashboardPage() {

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 lg:ml-16">
        <main className="p-4 md:p-6 lg:p-8">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold mb-2">Дэщборд</h1>
            <p className="text-primary-foreground">
              Добро пожаловать в панель управления сознанием
            </p>
          </div>

          {/* Map Section */}
          <div className="mt-6">
            <Card className="border border-divider">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  <h2 className="text-lg font-semibold">Карта с рисованием</h2>
                </div>
              </CardHeader>
              <CardBody className="p-0">
                <div className="p-4">
                  <p className="text-sm text-default-500 mb-4">
                    Используйте инструменты в правом верхнем углу карты для рисования точек и линий
                  </p>
                </div>
                <MapDraw height="600px" />
              </CardBody>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}

