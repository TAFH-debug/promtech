"use client";

import dynamic from "next/dynamic";
import { Sidebar } from "@/components/sidebar";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { MapPin } from "lucide-react";
import { useEffect, useState } from "react";
import { MapFiltersComponent } from "@/components/map-filters";
import { ObjectSearch } from "@/components/object-search";
import { fetchMapObjects, MapObject, MapFilters } from "@/lib/api";
import { Tabs, Tab } from "@heroui/tabs";

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
  const [mapObjects, setMapObjects] = useState<MapObject[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<MapFilters>({});

  useEffect(() => {
    const loadMapObjects = async () => {
      setLoading(true);
      try {
        const data = await fetchMapObjects(filters);
        console.log(data);
        setMapObjects(data);
      } catch (error) {
        console.error("Error fetching map objects:", error);
        setMapObjects([]);
      } finally {
        setLoading(false);
      }
    };

    loadMapObjects();
  }, [filters]);

  const handleFiltersChange = (newFilters: MapFilters) => {
    setFilters(newFilters);
  };

  const handleFiltersReset = () => {
    setFilters({});
  };

  // Статистика по критичности
  const stats = {
    total: mapObjects.length,
    high: mapObjects.filter((o) => o.criticality === "high").length,
    medium: mapObjects.filter((o) => o.criticality === "medium").length,
    normal: mapObjects.filter((o) => o.criticality === "normal").length,
    defects: mapObjects.filter((o) => o.status === "defect").length,
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 lg:ml-16">
        <main className="p-4 md:p-6 lg:p-8">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold mb-2">Картографическая визуализация</h1>
            <p className="text-primary-foreground">
              Визуализация объектов и диагностик на карте Казахстана
            </p>
          </div>

          {/* Statistics */}
          {mapObjects.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
              <Card className="border border-divider">
                <CardBody className="p-4">
                  <p className="text-sm text-default-500 mb-1">Всего объектов</p>
                  <p className="text-2xl font-bold">{stats.total}</p>
                </CardBody>
              </Card>
              <Card className="border border-divider">
                <CardBody className="p-4">
                  <p className="text-sm text-default-500 mb-1">Высокая критичность</p>
                  <p className="text-2xl font-bold text-red-600">{stats.high}</p>
                </CardBody>
              </Card>
              <Card className="border border-divider">
                <CardBody className="p-4">
                  <p className="text-sm text-default-500 mb-1">Средняя критичность</p>
                  <p className="text-2xl font-bold text-orange-600">{stats.medium}</p>
                </CardBody>
              </Card>
              <Card className="border border-divider">
                <CardBody className="p-4">
                  <p className="text-sm text-default-500 mb-1">Норма</p>
                  <p className="text-2xl font-bold text-green-600">{stats.normal}</p>
                </CardBody>
              </Card>
              <Card className="border border-divider">
                <CardBody className="p-4">
                  <p className="text-sm text-default-500 mb-1">С дефектами</p>
                  <p className="text-2xl font-bold text-red-600">{stats.defects}</p>
                </CardBody>
              </Card>
            </div>
          )}

          {/* Tabs for Map and Search */}
          <Tabs aria-label="Dashboard tabs" className="mb-6">
            <Tab key="map" title="Карта">
              {/* Map Filters */}
              <MapFiltersComponent
                filters={filters}
                onFiltersChange={handleFiltersChange}
                onReset={handleFiltersReset}
              />

              {/* Map Section */}
              <Card className="border border-divider">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-5 w-5" />
                      <h2 className="text-lg font-semibold">
                        Карта объектов ({mapObjects.length})
                      </h2>
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-green-500"></div>
                        <span>Норма</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                        <span>Средняя</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-500"></div>
                        <span>Высокая</span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardBody className="p-0">
                  <MapDraw height="700px" objects={mapObjects} filters={filters} />
                </CardBody>
              </Card>
            </Tab>
            <Tab key="search" title="Поиск и фильтры">
              <ObjectSearch />
            </Tab>
          </Tabs>
        </main>
      </div>
    </div>
  );
}

