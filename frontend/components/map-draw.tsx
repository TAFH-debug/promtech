"use client";

import React, { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, useMap, Marker, Polyline } from "react-leaflet";
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

interface MapDrawProps {
  height?: string;
}

interface Point {
  lat: number;
  lng: number;
  id: string;
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
          showArea: false,
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

// Предустановленные точки
const initialPoints: Point[] = [
  { id: "point-1", lat: 55.7558, lng: 37.6173 }, // Москва, Красная площадь
  { id: "point-2", lat: 55.7520, lng: 37.6156 }, // Москва, Кремль
  { id: "point-3", lat: 55.7517, lng: 37.6188 }, // Москва, ГУМ
  { id: "point-4", lat: 55.7495, lng: 37.6200 }, // Москва, Манежная площадь
];

// Предустановленные линии
const initialLines: Line[] = [
  {
    id: "line-1",
    points: [
      { id: "line1-point-1", lat: 55.7558, lng: 37.6173 },
      { id: "line1-point-2", lat: 55.7520, lng: 37.6156 },
      { id: "line1-point-3", lat: 55.7517, lng: 37.6188 },
    ],
  },
  {
    id: "line-2",
    points: [
      { id: "line2-point-1", lat: 55.7517, lng: 37.6188 },
      { id: "line2-point-2", lat: 55.7495, lng: 37.6200 },
    ],
  },
];

export function MapDraw({ height = "600px" }: MapDrawProps) {
  const [points, setPoints] = useState<Point[]>(initialPoints);
  const [lines, setLines] = useState<Line[]>(initialLines);

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
        center={[55.7558, 37.6173]} // Москва по умолчанию
        zoom={10}
        style={{ height: "100%", width: "100%" }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <DrawControl onDraw={handleDraw} initialPoints={initialPoints} initialLines={initialLines} />
        {points.map((point) => (
          <Marker key={point.id} position={[point.lat, point.lng]} />
        ))}
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

