"use client";

import React, { useEffect, useRef, useState, useMemo } from "react";
import { MapContainer, TileLayer, useMap, Marker, Polyline, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import "leaflet-draw";

// Fix for default marker icons in Next.js
if (typeof window !== "undefined") {
  delete (L.Icon.Default.prototype as any)._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
    iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  });
}

import { MapObject } from "@/lib/api";

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

interface DrawControlProps {
  onDraw: (type: string, data: any) => void;
  initialPoints?: Point[];
  initialLines?: Line[];
}

function DrawControl({ onDraw, initialPoints = [], initialLines = [] }: DrawControlProps) {
  const map = useMap();
  const drawnItemsRef = useRef<L.FeatureGroup>(new L.FeatureGroup());
  const initializedRef = useRef(false);

  useEffect(() => {
    if (!map || initializedRef.current) return;

    // Добавляем предустановленные точки и линии только один раз
    initialPoints.forEach((point) => {
      const marker = L.marker([point.lat, point.lng]);
      (marker as any)._leaflet_id = point.id;
      drawnItemsRef.current.addLayer(marker);
    });

    initialLines.forEach((line) => {
      const latlngs = line.points.map((p) => [p.lat, p.lng] as [number, number]);
      const polyline = L.polyline(latlngs, { color: "#3b82f6", weight: 4 });
      (polyline as any)._leaflet_id = line.id;
      drawnItemsRef.current.addLayer(polyline);
    });

    initializedRef.current = true;

    // Add the draw control
    const drawControl = new L.Control.Draw({
      position: "topright",
      draw: {
        marker: {
          icon: L.icon({
            iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
          }),
        },
        polyline: {
          allowIntersection: false,
          shapeOptions: {
            color: "#3b82f6",
            weight: 4,
          },
        },
        polygon: false,
        rectangle: false,
        circle: false,
        circlemarker: false,
      },
      edit: {
        featureGroup: drawnItemsRef.current,
        remove: true,
      },
    });

    map.addControl(drawControl);
    map.addLayer(drawnItemsRef.current);

    // Handle draw events
    const handleDrawCreated = (e: L.DrawEvents.Created) => {
      const layer = e.layer;
      drawnItemsRef.current.addLayer(layer);

      if (layer instanceof L.Marker) {
        const latlng = layer.getLatLng();
        onDraw("marker", {
          lat: latlng.lat,
          lng: latlng.lng,
          id: `marker-${Date.now()}`,
        });
      } else if (layer instanceof L.Polyline) {
        const latlngs = layer.getLatLngs() as L.LatLng[];
        onDraw("polyline", {
          points: latlngs.map((ll, idx) => ({
            lat: ll.lat,
            lng: ll.lng,
            id: `point-${Date.now()}-${idx}`,
          })),
          id: `line-${Date.now()}`,
        });
      }
    };

    const handleDrawDeleted = () => {
      // Handle deletion if needed
    };

    const handleDrawEdited = (e: L.DrawEvents.Edited) => {
      // Handle edit if needed
      const layers = e.layers;
      layers.eachLayer((layer) => {
        if (layer instanceof L.Marker) {
          const latlng = layer.getLatLng();
          onDraw("marker-updated", {
            lat: latlng.lat,
            lng: latlng.lng,
            id: (layer as any)._leaflet_id,
          });
        } else if (layer instanceof L.Polyline) {
          const latlngs = layer.getLatLngs() as L.LatLng[];
          onDraw("polyline-updated", {
            points: latlngs.map((ll, idx) => ({
              lat: ll.lat,
              lng: ll.lng,
              id: `point-${Date.now()}-${idx}`,
            })),
            id: (layer as any)._leaflet_id,
          });
        }
      });
    };

    map.on(L.Draw.Event.CREATED, handleDrawCreated);
    map.on(L.Draw.Event.DELETED, handleDrawDeleted);
    map.on(L.Draw.Event.EDITED, handleDrawEdited);

    return () => {
      map.removeControl(drawControl);
      map.off(L.Draw.Event.CREATED, handleDrawCreated);
      map.off(L.Draw.Event.DELETED, handleDrawDeleted);
      map.off(L.Draw.Event.EDITED, handleDrawEdited);
    };
  }, [map, onDraw, initialPoints, initialLines]);

  return null;
}

// Component to handle marker rendering and ensure proper cleanup
function MarkersGroup({ points }: { points: Point[] }) {
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
              </div>
            </Popup>
          </Marker>
        );
    });
  }, [points]);

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
  
  // Generate lines between pipeline sections of the same pipeline
  const pipelineLines = useMemo(() => {
    const lines: Line[] = [];
    
    // Filter only pipeline sections
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
    
    // For each pipeline, connect sections using a greedy nearest-neighbor approach
    // This ensures each section is connected to its nearest unconnected neighbor
    sectionsByPipeline.forEach((sections, pipelineId) => {
      if (sections.length < 2) return;
      
      // Track which sections are already connected (have at least one connection)
      const connectedSections = new Set<string>();
      const createdConnections = new Set<string>(); // Track pairs to avoid duplicates
      
      // For each section, find the nearest unconnected section
      sections.forEach((currentSection) => {
        // Find the nearest section that is not yet connected
        let nearest: Point | null = null;
        let minDistance = Infinity;
        
        sections.forEach((otherSection) => {
          if (currentSection.id === otherSection.id) return;
          
          // Check if this connection already exists (in either direction)
          const connectionKey1 = `${currentSection.id}-${otherSection.id}`;
          const connectionKey2 = `${otherSection.id}-${currentSection.id}`;
          if (createdConnections.has(connectionKey1) || createdConnections.has(connectionKey2)) {
            return;
          }
          
          // Calculate distance using Haversine formula
          const distance = calculateDistance(
            currentSection.lat,
            currentSection.lng,
            otherSection.lat,
            otherSection.lng
          );
          
          // Prefer connecting to unconnected sections, but allow connecting to connected ones if needed
          if (distance < minDistance) {
            minDistance = distance;
            nearest = otherSection;
          }
        });
        
        // Create a line between current section and nearest section
        if (nearest) {
          const connectionKey = `${currentSection.id}-${nearest.id}`;
          createdConnections.add(connectionKey);
          
          lines.push({
            id: `pipeline-${pipelineId}-${currentSection.id}-${nearest.id}`,
            points: [
              {
                id: `${currentSection.id}-start`,
                lat: currentSection.lat,
                lng: currentSection.lng,
              },
              {
                id: `${nearest.id}-end`,
                lat: nearest.lat,
                lng: nearest.lng,
              },
            ],
          });
          
          // Mark both sections as connected
          connectedSections.add(currentSection.id);
          connectedSections.add(nearest.id);
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

  const handleDraw = (type: string, data: any) => {
    if (type === "marker") {
      setPoints((prev) => [...prev, data]);
    } else if (type === "polyline") {
      setLines((prev) => [...prev, data]);
    } else if (type === "marker-updated") {
      setPoints((prev) =>
        prev.map((p) => (p.id === data.id ? { ...p, lat: data.lat, lng: data.lng } : p))
      );
    } else if (type === "polyline-updated") {
      setLines((prev) =>
        prev.map((l) => (l.id === data.id ? { ...l, points: data.points } : l))
      );
    }
  };

  return (
    <div className="w-full rounded-lg overflow-hidden border border-divider" style={{ height }}>
      <MapContainer
        center={[48.0196, 66.9237]} // Центр Казахстана
        zoom={6}
        style={{ height: "100%", width: "100%" }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <DrawControl onDraw={handleDraw} initialPoints={points} />
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

