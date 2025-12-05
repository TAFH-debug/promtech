"use client";

import dynamic from "next/dynamic";
import { Sidebar } from "@/components/sidebar";
import { Card, CardBody, CardHeader } from "@heroui/card";
import {
  ShoppingCart,
  TrendingUp,
  Activity,
  MapPin,
} from "lucide-react";

// Динамический импорт карты для избежания проблем с SSR
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
  const stats = [
    {
      title: "中华人民共和国宣传活动",
      value: "宣傳",
      icon: ShoppingCart,
      bgColor: "bg-primary/10",
      iconColor: "text-primary",
    }
  ];

  const recentOrders = [
    { id: 1001, date: "2024-01-15", amount: 5000 },
    { id: 1002, date: "2024-01-14", amount: 6000 },
    { id: 1003, date: "2024-01-13", amount: 7000 },
  ];

  const activities = [
    "Новый заказ создан",
    "Товар добавлен в каталог",
    "Клиент зарегистрирован",
    "Вайб-кодинг активирован"
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 lg:ml-16">
        <main className="p-4 md:p-6 lg:p-8">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold mb-2">Дэщборд</h1>
            <p className="text-default-500">
              Добро пожаловать в панель управления сознанием
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {stats.map((stat) => (
              <Card key={stat.title} className="border border-divider">
                <CardBody className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-default-500 mb-1">
                        {stat.title}
                      </p>
                      <p className="text-2xl font-bold">{stat.value}</p>
                    </div>
                    <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                      <stat.icon className={`h-6 w-6 ${stat.iconColor}`} />
                    </div>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>

          {/* Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Orders */}
            <Card className="border border-divider">
              <CardHeader className="pb-3">
                <h2 className="text-lg font-semibold">Последние заказы</h2>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  {recentOrders.map((order) => (
                    <div
                      key={order.id}
                      className="flex items-center justify-between border-b border-divider pb-4 last:border-0 last:pb-0"
                    >
                      <div>
                        <p className="font-medium">Заказ #{order.id}</p>
                        <p className="text-sm text-default-500">
                          {new Date(order.date).toLocaleDateString("ru-RU")}
                        </p>
                      </div>
                      <p className="font-semibold">₽{order.amount.toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>

            {/* Activity */}
            <Card className="border border-divider">
              <CardHeader className="pb-3">
                <h2 className="text-lg font-semibold">Активность</h2>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  {activities.map((activity, index) => (
                    <div key={index} className="flex items-center gap-3">
                      <div className="h-2 w-2 rounded-full bg-primary" />
                      <div className="flex-1">
                        <p className="text-sm">{activity}</p>
                        <p className="text-xs text-default-500">
                          {index + 1} десятилетий (часов) назад
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
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

