"use client";

import React, { useEffect, useRef, useState, useMemo } from "react";
import { MapContainer, TileLayer, useMap, Marker, Polyline, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import "leaflet-draw";
import { FileDown, Loader2 } from "lucide-react";

// Fix for default marker icons in Next.js
if (typeof window !== "undefined") {
  delete (L.Icon.Default.prototype as any)._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
    iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  });
}

import { MapObject, downloadPipelineReport, captureMapImage } from "@/lib/api";
import html2canvas from 'html2canvas-pro';

interface MapDrawProps {
  height?: string;
  objects?: MapObject[];
  filters?: {
    pipeline_id?: string;
    method?: string;
    date_from?: string;
    date_to?: string;
    param_min?: number;
    param_max?: number;
  };
}

interface Point {
  lat: number;
  lng: number;
  id: string;
  name?: string;
  description?: string;
  objectType?: string;
  pipelineId?: string;
  year?: number;
  material?: string;
  status?: string;
  criticality?: string;
  popupData?: MapObject["popup_data"];
}

// Helper function to get marker color based on criticality
function getMarkerColor(criticality: string): string {
  switch (criticality) {
    case "high":
      return "#ef4444"; // red
    case "medium":
      return "#f59e0b"; // orange
    case "normal":
      return "#10b981"; // green
    default:
      return "#6b7280"; // gray
  }
}

// Helper function to create custom icon
function createCustomIcon(color: string) {
  return L.divIcon({
    className: "custom-marker",
    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
}

// Calculate distance between two points using Haversine formula (in kilometers)
function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth's radius in kilometers
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) *
      Math.cos(lat2 * (Math.PI / 180)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

interface Line {
  points: Point[];
  id: string;
}

// Component to handle marker rendering and ensure proper cleanup
// Popup content component
function PopupContent({ point, onDownloadReport, isDownloading }: { 
  point: Point; 
  onDownloadReport: (pipelineId: string) => void;
  isDownloading: boolean;
}) {
  return (
    <div className="p-2 min-w-[250px]">
      <h3 className="font-bold text-lg mb-2">{point.name || `Точка ${point.id}`}</h3>
      {point.objectType && (
        <p className="text-sm mb-1">
          <span className="font-semibold">Тип:</span> {point.objectType}
        </p>
      )}
      {point.pipelineId && (
        <p className="text-sm mb-1">
          <span className="font-semibold">Трубопровод:</span> {point.pipelineId}
        </p>
      )}
      {point.year && (
        <p className="text-sm mb-1">
          <span className="font-semibold">Год:</span> {point.year}
        </p>
      )}
      {point.material && (
        <p className="text-sm mb-1">
          <span className="font-semibold">Материал:</span> {point.material}
        </p>
      )}
      {point.popupData && (
        <>
          {point.popupData.last_check_date && (
            <p className="text-sm mb-1">
              <span className="font-semibold">Последняя проверка:</span> {point.popupData.last_check_date}
            </p>
          )}
          {point.popupData.method && (
            <p className="text-sm mb-1">
              <span className="font-semibold">Метод:</span> {point.popupData.method}
            </p>
          )}
          {point.popupData.quality_grade && (
            <p className="text-sm mb-1">
              <span className="font-semibold">Оценка:</span> {point.popupData.quality_grade}
            </p>
          )}
          {point.popupData.max_depth !== undefined && point.popupData.max_depth !== null && (
            <p className="text-sm mb-1">
              <span className="font-semibold">Макс. глубина:</span> {point.popupData.max_depth.toFixed(2)} мм
            </p>
          )}
          {point.popupData.defect_count > 0 && (
            <p className="text-sm mb-1 text-red-600">
              <span className="font-semibold">Дефектов:</span> {point.popupData.defect_count}
            </p>
          )}
          {point.criticality && (
            <p className="text-sm mb-1">
              <span className="font-semibold">Критичность:</span>{" "}
              <span
                className={`inline-block px-2 py-1 rounded text-xs ${
                  point.criticality === "high"
                    ? "bg-red-100 text-red-800"
                    : point.criticality === "medium"
                    ? "bg-orange-100 text-orange-800"
                    : "bg-green-100 text-green-800"
                }`}
              >
                {point.criticality === "high"
                  ? "Высокая"
                  : point.criticality === "medium"
                  ? "Средняя"
                  : "Нормальная"}
              </span>
            </p>
          )}
        </>
      )}
      {point.status && (
        <p className="text-sm mb-1">
          <span className="font-semibold">Статус:</span>{" "}
          {point.status === "defect"
            ? "Дефект"
            : point.status === "clean"
            ? "Чисто"
            : "Неизвестно"}
        </p>
      )}
      <p className="text-xs text-gray-500 mt-2">
        Координаты: {point.lat.toFixed(6)}, {point.lng.toFixed(6)}
      </p>
      {point.pipelineId && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <button
            onClick={() => onDownloadReport(point.pipelineId!)}
            disabled={isDownloading}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-primary text-white rounded hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
          >
            {isDownloading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Загрузка...</span>
              </>
            ) : (
              <>
                <FileDown className="h-4 w-4" />
                <span>Скачать отчет {point.pipelineId}</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

function MarkersGroup({ points }: { points: Point[] }) {
  const [downloadingReports, setDownloadingReports] = useState<Set<string>>(new Set());

  const handleDownloadReport = async (pipelineId: string) => {
    if (!pipelineId || downloadingReports.has(pipelineId)) return;
    
    setDownloadingReports((prev) => new Set(prev).add(pipelineId));
    try {
      const mapElement = document.querySelector('.leaflet-container') as HTMLElement;

      if (!mapElement) {
        alert("Карта не найдена!");
        return;
      }
      
      const controls = mapElement.querySelector('.leaflet-control-container') as HTMLElement;
      const popup = mapElement.querySelector('.leaflet-popup-pane') as HTMLElement;
      if (controls) controls.style.display = 'none';
      if (popup) popup.style.display = 'none';
      const canvas = await html2canvas(mapElement, {
        useCORS: true, 
        allowTaint: true,
        logging: false,
        scale: 2
      });

      if (controls) controls.style.display = 'block';
      if (popup) popup.style.display = 'block';
      const mapImage = canvas.toDataURL('image/png');

      await downloadPipelineReport(pipelineId, mapImage!);
    } catch (error) {
      console.error(`Error downloading report for ${pipelineId}:`, error);
      alert(`Ошибка при скачивании отчета для ${pipelineId} ${error}`);
    } finally {
      setDownloadingReports((prev) => {
        const newSet = new Set(prev);
        newSet.delete(pipelineId);
        return newSet;
      });
    }
  };

  // Use useMemo to ensure markers are properly recreated when points change
  const markers = useMemo(() => {
    return points.map((point) => {
      const color = point.criticality ? getMarkerColor(point.criticality) : getMarkerColor(point.status || "normal");
      const icon = createCustomIcon(color);
      
      return (
        <Marker 
          key={point.id}
          position={[point.lat, point.lng]} 
          icon={icon}
        >
            <Popup>
              <PopupContent
                point={point}
                onDownloadReport={handleDownloadReport}
                isDownloading={downloadingReports.has(point.pipelineId || "")}
              />
            </Popup>
          </Marker>
        );
    });
  }, [points, downloadingReports]);

  return <>{markers}</>;
}

export function MapDraw({ height = "600px", objects = [], filters }: MapDrawProps) {
  // Convert MapObject to Point format with useMemo to avoid unnecessary recalculations
  const objectPoints: Point[] = useMemo(() => {
    return objects.map((obj) => ({
      id: `object-${obj.id}`,
      lat: obj.lat,
      lng: obj.lon,
      name: obj.popup_data.object_name,
      objectType: obj.popup_data.object_type,
      pipelineId: obj.pipeline_id,
      year: obj.popup_data.year,
      material: obj.popup_data.material,
      status: obj.status,
      criticality: obj.criticality,
      popupData: obj.popup_data,
    }));
  }, [objects]);

  const [points, setPoints] = useState<Point[]>(
    objects.length > 0 ? objectPoints : []
  );
  const pipelineLines = useMemo(() => {
    const lines: Line[] = [];
    
    const pipelineSections = points.filter(
      (point) => point.objectType === "pipeline section" && point.pipelineId
    );
    
    // Group by pipeline_id
    const sectionsByPipeline = new Map<string, Point[]>();
    pipelineSections.forEach((section) => {
      const pipelineId = section.pipelineId!;
      if (!sectionsByPipeline.has(pipelineId)) {
        sectionsByPipeline.set(pipelineId, []);
      }
      sectionsByPipeline.get(pipelineId)!.push(section);
    });
    sectionsByPipeline.forEach((sections, pipelineId) => {
      if (sections.length < 2) return;
      
      const connectedSections = new Set<string>();
      const createdConnections = new Set<string>();
      
      sections.forEach((currentSection) => {
        let nearest: Point | null = null;
        let minDistance = Infinity;
        
        sections.forEach((otherSection) => {
          if (currentSection.id === otherSection.id) return;
          
          const connectionKey1 = `${currentSection.id}-${otherSection.id}`;
          const connectionKey2 = `${otherSection.id}-${currentSection.id}`;
          if (createdConnections.has(connectionKey1) || createdConnections.has(connectionKey2) || connectedSections.has(otherSection.id)) {
            return;
          }
          
          const distance = calculateDistance(
            currentSection.lat,
            currentSection.lng,
            otherSection.lat,
            otherSection.lng
          );
          
          if (distance < minDistance) {
            minDistance = distance;
            nearest = otherSection;
          }
        });
        
        if (nearest) {
          const nearestPoint: Point = nearest;
          const connectionKey = `${currentSection.id}-${nearestPoint.id}`;
          createdConnections.add(connectionKey);
          
          lines.push({
            id: `pipeline-${pipelineId}-${currentSection.id}-${nearestPoint.id}`,
            points: [
              {
                id: `${currentSection.id}-start`,
                lat: currentSection.lat,
                lng: currentSection.lng,
              },
              {
                id: `${nearestPoint.id}-end`,
                lat: nearestPoint.lat,
                lng: nearestPoint.lng,
              },
            ],
          });
          
          connectedSections.add(currentSection.id);
          connectedSections.add(nearestPoint.id);
        }
      });
    });
    return lines;
  }, [points]);

  const [lines, setLines] = useState<Line[]>([]);
  // Update points when objects change - use useMemo to create a new array reference
  const pointsFromObjects = useMemo(() => {
    if (objects.length > 0) {
      return objects.map((obj) => ({
        id: `object-${obj.id}`,
        lat: obj.lat,
        lng: obj.lon,
        name: obj.popup_data.object_name,
        objectType: obj.popup_data.object_type,
        pipelineId: obj.pipeline_id,
        year: obj.popup_data.year,
        material: obj.popup_data.material,
        status: obj.status,
        criticality: obj.criticality,
        popupData: obj.popup_data,
      }));
    }
    return [];
  }, [objects]);

  // Update points state when objects change
  useEffect(() => {
    setPoints(pointsFromObjects);
  }, [pointsFromObjects]);

  // Update lines when pipeline lines change
  useEffect(() => {
    setLines(pipelineLines);
  }, [pipelineLines]);

  return (
    <div className="w-full rounded-lg overflow-hidden border border-divider" style={{ height }}>
      <MapContainer
        center={[51.1801, 71.446]} // Центр Казахстана
        zoom={6}
        minZoom={12}
        maxZoom={18}
        style={{ height: "100%", width: "100%" }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MarkersGroup points={points} />
        {lines.map((line) => (
          <Polyline
            key={line.id}
            positions={line.points.map((p) => [p.lat, p.lng])}
            color="#3b82f6"
            weight={4}
          />
        ))}
      </MapContainer>
    </div>
  );
}

