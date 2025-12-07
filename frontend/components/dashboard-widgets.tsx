"use client";

import { Card, CardBody, CardHeader } from "@heroui/card";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import {
  DashboardStats,
  DefectByMethod,
  DefectByCriticality,
  TopRisk,
  InspectionsByYear,
} from "@/lib/api";
import { AlertTriangle, TrendingUp, Calendar, Activity } from "lucide-react";

const COLORS = {
  high: "#ef4444",
  medium: "#f97316",
  normal: "#22c55e",
  unknown: "#6b7280",
};

const CHART_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#6366f1", "#14b8a6"];

interface DashboardWidgetsProps {
  stats: DashboardStats;
}

export function DefectsByMethodWidget({ data }: { data: DefectByMethod[] }) {
  return (
    <Card className="border border-divider">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Распределение дефектов по методам</h3>
        </div>
      </CardHeader>
      <CardBody>
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="method" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[300px] text-default-400">
            <p>Нет данных</p>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

export function DefectsByCriticalityWidget({ data }: { data: DefectByCriticality[] }) {
  const chartData = data.map((item) => ({
    name: item.criticality === "high" ? "Высокая" : item.criticality === "medium" ? "Средняя" : item.criticality === "normal" ? "Норма" : "Неизвестно",
    value: item.count,
    criticality: item.criticality,
  }));

  return (
    <Card className="border border-divider">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Распределение по критичности</h3>
        </div>
      </CardHeader>
      <CardBody>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[entry.criticality as keyof typeof COLORS] || COLORS.unknown}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[300px] text-default-400">
            <p>Нет данных</p>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

export function TopRisksWidget({ data }: { data: TopRisk[] }) {
  const getCriticalityColor = (criticality?: string) => {
    if (criticality === "high") return "text-red-600";
    if (criticality === "medium") return "text-orange-600";
    if (criticality === "normal") return "text-green-600";
    return "text-default-400";
  };

  const getCriticalityLabel = (criticality?: string) => {
    if (criticality === "high") return "Высокая";
    if (criticality === "medium") return "Средняя";
    if (criticality === "normal") return "Норма";
    return "Неизвестно";
  };

  return (
    <Card className="border border-divider">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Топ-5 рисков</h3>
        </div>
      </CardHeader>
      <CardBody>
        {data.length > 0 ? (
          <div className="space-y-4">
            {data.map((risk, index) => (
              <div
                key={risk.object_id}
                className="flex items-center justify-between p-3 border border-divider rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-default-100 font-bold">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-semibold">{risk.object_name}</p>
                    {risk.pipeline_id && (
                      <p className="text-sm text-default-500">{risk.pipeline_id}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div>
                    <p className="text-default-500">Критичность</p>
                    <p className={`font-semibold ${getCriticalityColor(risk.criticality)}`}>
                      {getCriticalityLabel(risk.criticality)}
                    </p>
                  </div>
                  <div>
                    <p className="text-default-500">Дефектов</p>
                    <p className="font-semibold">{risk.defect_count}</p>
                  </div>
                  {risk.max_depth !== undefined && risk.max_depth !== null && (
                    <div>
                      <p className="text-default-500">Макс. глубина</p>
                      <p className="font-semibold">{risk.max_depth.toFixed(2)}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-[300px] text-default-400">
            <p>Нет данных</p>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

export function InspectionsByYearWidget({ data }: { data: InspectionsByYear[] }) {
  return (
    <Card className="border border-divider">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Количество обследований по годам</h3>
        </div>
      </CardHeader>
      <CardBody>
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[300px] text-default-400">
            <p>Нет данных</p>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

export function DashboardWidgets({ stats }: DashboardWidgetsProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DefectsByMethodWidget data={stats.defects_by_method} />
        <DefectsByCriticalityWidget data={stats.defects_by_criticality} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TopRisksWidget data={stats.top_risks} />
        <InspectionsByYearWidget data={stats.inspections_by_year} />
      </div>
    </div>
  );
}

