"use client";

import { Card, CardBody, CardHeader } from "@heroui/card";
import { MLMetrics } from "@/lib/api";
import { Brain, TrendingUp, Users, Target, Clock } from "lucide-react";

interface MLMetricsProps {
  metrics: MLMetrics[];
  loading: boolean;
}

export function MLMetricsWidget({ metrics, loading }: MLMetricsProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("ru-RU", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getClassMetrics = (report: any, className: string) => {
    if (!report || !report[className]) return null;
    return report[className];
  };

  if (loading) {
    return (
      <Card className="border border-divider">
        <CardBody className="p-8">
          <div className="flex items-center justify-center">
            <p className="text-default-400">Загрузка метрик...</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (metrics.length === 0) {
    return (
      <Card className="border border-divider">
        <CardBody className="p-8">
          <div className="flex flex-col items-center justify-center text-default-400">
            <Brain className="h-12 w-12 mb-4 opacity-50" />
            <p>Метрики обучения модели отсутствуют</p>
            <p className="text-sm mt-2">Метрики появятся после импорта диагностических данных</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  const latest = metrics[0];

  return (
    <div className="space-y-6">
      {/* Latest Metrics Summary */}
      <Card className="border border-divider">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            <h3 className="text-lg font-semibold">Последние метрики обучения</h3>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 border border-divider rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                <p className="text-sm text-default-500">Точность обучения</p>
              </div>
              <p className="text-2xl font-bold text-primary">
                {(latest.training_accuracy * 100).toFixed(2)}%
              </p>
            </div>
            <div className="p-4 border border-divider rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4 text-success" />
                <p className="text-sm text-default-500">Точность теста</p>
              </div>
              <p className="text-2xl font-bold text-success">
                {(latest.test_accuracy * 100).toFixed(2)}%
              </p>
            </div>
            <div className="p-4 border border-divider rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Users className="h-4 w-4 text-default-400" />
                <p className="text-sm text-default-500">Обучающих примеров</p>
              </div>
              <p className="text-2xl font-bold">{latest.train_samples}</p>
            </div>
            <div className="p-4 border border-divider rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Users className="h-4 w-4 text-default-400" />
                <p className="text-sm text-default-500">Тестовых примеров</p>
              </div>
              <p className="text-2xl font-bold">{latest.test_samples}</p>
            </div>
          </div>

          {latest.predicted_count > 0 && (
            <div className="mb-4 p-4 bg-default-50 rounded-lg">
              <p className="text-sm text-default-500 mb-2">Предсказано меток</p>
              <p className="text-xl font-bold mb-3">{latest.predicted_count}</p>
              {Object.keys(latest.label_distribution).length > 0 && (
                <div className="flex gap-4">
                  {Object.entries(latest.label_distribution).map(([label, count]) => (
                    <div key={label} className="flex items-center gap-2">
                      <span className="text-sm font-semibold capitalize">{label}:</span>
                      <span className="text-sm">{count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="flex items-center gap-2 text-sm text-default-500">
            <Clock className="h-4 w-4" />
            <span>Обучено: {formatDate(latest.created_at)}</span>
          </div>
        </CardBody>
      </Card>

      {/* Detailed Classification Report */}
      <Card className="border border-divider">
        <CardHeader className="pb-3">
          <h3 className="text-lg font-semibold">Детальный отчет по классам (Тест)</h3>
        </CardHeader>
        <CardBody>
          {latest.test_report && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-divider">
                    <th className="text-left p-2">Класс</th>
                    <th className="text-right p-2">Precision</th>
                    <th className="text-right p-2">Recall</th>
                    <th className="text-right p-2">F1-score</th>
                    <th className="text-right p-2">Support</th>
                  </tr>
                </thead>
                <tbody>
                  {["normal", "medium", "high"].map((className) => {
                    const classMetrics = getClassMetrics(latest.test_report, className);
                    if (!classMetrics) return null;
                    return (
                      <tr key={className} className="border-b border-divider">
                        <td className="p-2 font-semibold capitalize">{className}</td>
                        <td className="text-right p-2">
                          {classMetrics.precision?.toFixed(3) || "N/A"}
                        </td>
                        <td className="text-right p-2">
                          {classMetrics.recall?.toFixed(3) || "N/A"}
                        </td>
                        <td className="text-right p-2">
                          {classMetrics["f1-score"]?.toFixed(3) || "N/A"}
                        </td>
                        <td className="text-right p-2">{classMetrics.support || 0}</td>
                      </tr>
                    );
                  })}
                  {latest.test_report["macro avg"] && (
                    <tr className="border-t-2 border-divider font-semibold">
                      <td className="p-2">Macro avg</td>
                      <td className="text-right p-2">
                        {latest.test_report["macro avg"].precision?.toFixed(3) || "N/A"}
                      </td>
                      <td className="text-right p-2">
                        {latest.test_report["macro avg"].recall?.toFixed(3) || "N/A"}
                      </td>
                      <td className="text-right p-2">
                        {latest.test_report["macro avg"]["f1-score"]?.toFixed(3) || "N/A"}
                      </td>
                      <td className="text-right p-2">
                        {latest.test_report["macro avg"].support || 0}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* History */}
      {metrics.length > 1 && (
        <Card className="border border-divider">
          <CardHeader className="pb-3">
            <h3 className="text-lg font-semibold">История обучения</h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {metrics.slice(1).map((metric) => (
                <div
                  key={metric.metric_id}
                  className="border border-divider rounded-lg p-4 hover:bg-default-50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-4">
                      <div>
                        <p className="text-sm text-default-500">Точность обучения</p>
                        <p className="font-semibold">{(metric.training_accuracy * 100).toFixed(2)}%</p>
                      </div>
                      <div>
                        <p className="text-sm text-default-500">Точность теста</p>
                        <p className="font-semibold">{(metric.test_accuracy * 100).toFixed(2)}%</p>
                      </div>
                      <div>
                        <p className="text-sm text-default-500">Примеров</p>
                        <p className="font-semibold">
                          {metric.train_samples} / {metric.test_samples}
                        </p>
                      </div>
                    </div>
                    <div className="text-sm text-default-500">
                      {formatDate(metric.created_at)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

