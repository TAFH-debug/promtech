"use client";

import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Select, SelectItem } from "@heroui/select";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { MapFilters } from "@/lib/api";
import { Search, Filter, X } from "lucide-react";

interface MapFiltersProps {
  filters: MapFilters;
  onFiltersChange: (filters: MapFilters) => void;
  onReset: () => void;
}

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

export function MapFiltersComponent({
  filters,
  onFiltersChange,
  onReset,
}: MapFiltersProps) {
  const updateFilter = (key: keyof MapFilters, value: string | number | undefined) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  return (
    <Card className="border border-divider mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            <h3 className="text-lg font-semibold">Фильтры</h3>
          </div>
          <Button
            size="sm"
            variant="light"
            onPress={onReset}
            startContent={<X className="h-4 w-4" />}
          >
            Сбросить
          </Button>
        </div>
      </CardHeader>
      <CardBody>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Pipeline Filter */}
          <Select
            label="Трубопровод"
            placeholder="Выберите трубопровод"
            selectedKeys={filters.pipeline_id ? [filters.pipeline_id] : []}
            onSelectionChange={(keys) => {
              const value = Array.from(keys)[0] as string | undefined;
              updateFilter("pipeline_id", value);
            }}
          >
            {PIPELINES.map((pipeline) => (
              <SelectItem key={pipeline} value={pipeline}>
                {pipeline}
              </SelectItem>
            ))}
          </Select>

          {/* Method Filter */}
          <Select
            label="Метод контроля"
            placeholder="Выберите метод"
            selectedKeys={filters.method ? [filters.method] : []}
            onSelectionChange={(keys) => {
              const value = Array.from(keys)[0] as string | undefined;
              updateFilter("method", value);
            }}
          >
            {METHODS.map((method) => (
              <SelectItem key={method} value={method}>
                {method}
              </SelectItem>
            ))}
          </Select>

          {/* Date From */}
          <Input
            type="date"
            label="Дата от"
            value={filters.date_from || ""}
            onChange={(e) => updateFilter("date_from", e.target.value || undefined)}
          />

          {/* Date To */}
          <Input
            type="date"
            label="Дата до"
            value={filters.date_to || ""}
            onChange={(e) => updateFilter("date_to", e.target.value || undefined)}
          />

          {/* Parameter Min */}
          <Input
            type="number"
            label="Глубина от (мм)"
            value={filters.param_min?.toString() || ""}
            onChange={(e) =>
              updateFilter(
                "param_min",
                e.target.value ? parseFloat(e.target.value) : undefined
              )
            }
          />

          {/* Parameter Max */}
          <Input
            type="number"
            label="Глубина до (мм)"
            value={filters.param_max?.toString() || ""}
            onChange={(e) =>
              updateFilter(
                "param_max",
                e.target.value ? parseFloat(e.target.value) : undefined
              )
            }
          />
        </div>
      </CardBody>
    </Card>
  );
}

