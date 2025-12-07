"use client";

import { Input } from "@heroui/input";
import { Select, SelectItem } from "@heroui/select";
import { Button } from "@heroui/button";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from "@heroui/table";
import { ObjectSearchParams, ObjectTableRow, searchObjects, downloadPipelineReport } from "@/lib/api";
import { Search, ArrowUpDown, FileDown, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";

const PIPELINES = ["MT-01", "MT-02", "MT-03"];
const METHODS = [
  "VIK",
  "PVK",
  "MPK",
  "UZK",
  "RGK",
  "TVK",
  "VIBRO",
  "MFL",
  "TFI",
  "GEO",
  "UTWM",
];

export function ObjectSearch() {
  const [searchParams, setSearchParams] = useState<ObjectSearchParams>({
    page: 1,
    size: 10,
    sort_by: "date",
    order: "desc",
  });
  const [results, setResults] = useState<ObjectTableRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloadingReports, setDownloadingReports] = useState<Set<string>>(new Set());

  const handleSearch = async () => {
    setLoading(true);
    try {
      const data = await searchObjects(searchParams);
      setResults(data);
    } catch (error) {
      console.error("Error searching objects:", error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, [searchParams.page, searchParams.size, searchParams.sort_by, searchParams.order]);

  const updateParam = (key: keyof ObjectSearchParams, value: any) => {
    setSearchParams({ ...searchParams, [key]: value });
  };

  const handleDownloadReport = async (pipelineId: string) => {
    if (!pipelineId || downloadingReports.has(pipelineId)) return;
    
    setDownloadingReports((prev) => new Set(prev).add(pipelineId));
    try {
      await downloadPipelineReport(pipelineId);
    } catch (error) {
      console.error(`Error downloading report for ${pipelineId}:`, error);
      alert(`Ошибка при скачивании отчета для ${pipelineId}`);
    } finally {
      setDownloadingReports((prev) => {
        const newSet = new Set(prev);
        newSet.delete(pipelineId);
        return newSet;
      });
    }
  };

  // Get unique pipeline IDs from results
  const uniquePipelines = Array.from(
    new Set(results.filter(r => r.pipeline_id).map(r => r.pipeline_id!))
  );

  return (
    <Card className="border border-divider">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Поиск и фильтрация объектов</h3>
        </div>
      </CardHeader>
      <CardBody>
        {/* Search Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <Input
            placeholder="Поиск по названию объекта"
            value={searchParams.search || ""}
            onChange={(e) => updateParam("search", e.target.value || undefined)}
            startContent={<Search className="h-4 w-4" />}
          />

          <Select
            label="Трубопровод"
            placeholder="Все"
            selectedKeys={searchParams.pipeline_id ? [searchParams.pipeline_id] : []}
            onSelectionChange={(keys) => {
              const value = Array.from(keys)[0] as string | undefined;
              updateParam("pipeline_id", value);
            }}
          >
            {PIPELINES.map((pipeline) => (
              <SelectItem key={pipeline}>
                {pipeline}
              </SelectItem>
            ))}
          </Select>

          <Select
            label="Метод"
            placeholder="Все"
            selectedKeys={searchParams.method ? [searchParams.method] : []}
            onSelectionChange={(keys) => {
              const value = Array.from(keys)[0] as string | undefined;
              updateParam("method", value);
            }}
          >
            {METHODS.map((method) => (
              <SelectItem key={method}>
                {method}
              </SelectItem>
            ))}
          </Select>

          <Input
            placeholder="Тип дефекта"
            value={searchParams.defect_type || ""}
            onChange={(e) => updateParam("defect_type", e.target.value || undefined)}
          />
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-4 mb-4">
          <Select
            label="Сортировка"
            selectedKeys={[searchParams.sort_by || "date"]}
            onSelectionChange={(keys) => {
              const value = Array.from(keys)[0] as string;
              updateParam("sort_by", value as "date" | "depth" | "name");
            }}
            className="w-40"
          >
            <SelectItem key="date">
              По дате
            </SelectItem>
            <SelectItem key="depth">
              По глубине
            </SelectItem>
            <SelectItem key="name">
              По названию
            </SelectItem>
          </Select>

          <Select
            label="Порядок"
            selectedKeys={[searchParams.order || "desc"]}
            onSelectionChange={(keys) => {
              const value = Array.from(keys)[0] as string;
              updateParam("order", value as "asc" | "desc");
            }}
            className="w-32"
          >
            <SelectItem key="desc">
              Убывание
            </SelectItem>
            <SelectItem key="asc">
              Возрастание
            </SelectItem>
          </Select>

          <Button
            color="primary"
            onPress={handleSearch}
            isLoading={loading}
            startContent={!loading && <Search className="h-4 w-4" />}
          >
            Поиск
          </Button>
        </div>

        {/* Results Table */}
        <div className="overflow-x-auto">
          <Table aria-label="Objects table">
            <TableHeader>
              <TableColumn>ID</TableColumn>
              <TableColumn>Название</TableColumn>
              <TableColumn>Трубопровод</TableColumn>
              <TableColumn>Тип</TableColumn>
              <TableColumn>Дата проверки</TableColumn>
              <TableColumn>Метод</TableColumn>
              <TableColumn>Статус</TableColumn>
              <TableColumn>Тип дефекта</TableColumn>
              <TableColumn>Глубина (мм)</TableColumn>
              <TableColumn>Отчет</TableColumn>
            </TableHeader>
            <TableBody emptyContent="Нет данных">
              {results.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>{row.id}</TableCell>
                  <TableCell>{row.object_name}</TableCell>
                  <TableCell>{row.pipeline_id || "N/A"}</TableCell>
                  <TableCell>{row.object_type}</TableCell>
                  <TableCell>
                    {row.last_check_date
                      ? new Date(row.last_check_date).toLocaleDateString("ru-RU")
                      : "N/A"}
                  </TableCell>
                  <TableCell>{row.method || "N/A"}</TableCell>
                  <TableCell>
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        row.status === "defect"
                          ? "bg-red-100 text-red-800"
                          : row.status === "clean"
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {row.status === "defect"
                        ? "Дефект"
                        : row.status === "clean"
                        ? "Чисто"
                        : "Неизвестно"}
                    </span>
                  </TableCell>
                  <TableCell>{row.defect_type || "N/A"}</TableCell>
                  <TableCell>{row.max_depth.toFixed(2)}</TableCell>
                  <TableCell>
                    {row.pipeline_id ? (
                      <Button
                        size="sm"
                        variant="flat"
                        color="primary"
                        isIconOnly
                        onPress={() => handleDownloadReport(row.pipeline_id!)}
                        isLoading={downloadingReports.has(row.pipeline_id)}
                        isDisabled={downloadingReports.has(row.pipeline_id)}
                        title={`Скачать отчет для ${row.pipeline_id}`}
                      >
                        {downloadingReports.has(row.pipeline_id) ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <FileDown className="h-4 w-4" />
                        )}
                      </Button>
                    ) : (
                      <span className="text-default-400 text-xs">N/A</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pipeline Reports Section */}
        {uniquePipelines.length > 0 && (
          <div className="mt-6">
            <Card className="border border-divider">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <FileDown className="h-5 w-5" />
                  <h3 className="text-lg font-semibold">Отчеты по трубопроводам</h3>
                </div>
              </CardHeader>
              <CardBody>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {uniquePipelines.map((pipelineId) => (
                    <div
                      key={pipelineId}
                      className="flex items-center justify-between p-3 border border-divider rounded-lg hover:bg-default-50 transition-colors"
                    >
                      <span className="font-semibold">{pipelineId}</span>
                      <Button
                        size="sm"
                        color="primary"
                        variant="flat"
                        onPress={() => handleDownloadReport(pipelineId)}
                        isLoading={downloadingReports.has(pipelineId)}
                        isDisabled={downloadingReports.has(pipelineId)}
                        startContent={
                          !downloadingReports.has(pipelineId) && (
                            <FileDown className="h-4 w-4" />
                          )
                        }
                      >
                        {downloadingReports.has(pipelineId) ? "Загрузка..." : "Скачать PDF"}
                      </Button>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          </div>
        )}

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-default-500">
            Показано {results.length} из результатов
          </p>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="flat"
              isDisabled={searchParams.page === 1}
              onPress={() => updateParam("page", (searchParams.page || 1) - 1)}
            >
              Назад
            </Button>
            <Button
              size="sm"
              variant="flat"
              isDisabled={results.length < (searchParams.size || 10)}
              onPress={() => {
                updateParam("page", (searchParams.page || 1) + 1);
                handleSearch();
              }}
            >
              Вперед
            </Button>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

