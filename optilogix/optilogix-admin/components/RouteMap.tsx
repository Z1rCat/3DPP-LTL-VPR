
import React, { useEffect, useRef } from 'react';
import { DeliveryPoint } from '../types';
import { MapPin, Home, Navigation, Layers } from 'lucide-react';
import L from 'leaflet';

interface RouteMapProps {
  points: DeliveryPoint[];
  highlightRoute: boolean;
}

export const RouteMap: React.FC<RouteMapProps> = ({ points, highlightRoute }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.LayerGroup | null>(null);
  const routeLineRef = useRef<L.Polyline | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize Map only once
    if (!mapInstanceRef.current) {
      // Center on Chengdu
      const map = L.map(mapContainerRef.current, {
        center: [30.6586, 104.0648],
        zoom: 11,
        zoomControl: false,
        attributionControl: false
      });

      // Add OpenStreetMap Tiles (Chengdu)
      // Using a standard OSM tile server. For production, use a paid provider like Mapbox/GMap or a CDN.
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map);
      
      // Add Zoom Control to bottom right
      L.control.zoom({ position: 'bottomright' }).addTo(map);

      mapInstanceRef.current = map;
      markersRef.current = L.layerGroup().addTo(map);
    }

    const map = mapInstanceRef.current;
    const markersLayer = markersRef.current;
    
    if (!map || !markersLayer) return;

    // Clear existing layers
    markersLayer.clearLayers();
    if (routeLineRef.current) {
      routeLineRef.current.remove();
      routeLineRef.current = null;
    }

    // 1. Add Markers
    const depot = points.find(p => p.id === 'DEPOT');
    const deliveries = points.filter(p => p.id !== 'DEPOT').sort((a, b) => (a.sequence || 0) - (b.sequence || 0));
    
    // Helper to create custom SVG icons using Lucide
    const createIcon = (color: string, type: 'DEPOT' | 'POINT', seq?: number) => {
        const html = `
          <div style="
            background-color: ${color}; 
            width: ${type === 'DEPOT' ? '32px' : '24px'}; 
            height: ${type === 'DEPOT' ? '32px' : '24px'}; 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            border: 2px solid white; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            color: white;
            font-weight: bold;
            font-size: 10px;
            font-family: sans-serif;
          ">
            ${type === 'DEPOT' 
                ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>' 
                : (seq || '')
            }
          </div>
          <div style="
            position: absolute; 
            top: ${type === 'DEPOT' ? '34px' : '26px'}; 
            left: 50%; 
            transform: translateX(-50%); 
            background: white; 
            padding: 2px 6px; 
            border-radius: 4px; 
            font-size: 10px; 
            white-space: nowrap; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            font-weight: bold;
            color: #334155;
          ">
            ${type === 'DEPOT' ? '中央仓' : ''}
          </div>
        `;
        return L.divIcon({
            className: 'custom-marker',
            html: html,
            iconSize: [30, 30],
            iconAnchor: [15, 30]
        });
    };

    points.forEach(p => {
        const isDepot = p.id === 'DEPOT';
        // Highlight color logic
        let color = '#94a3b8'; // Default gray
        if (isDepot) color = '#faad14'; // Depot Orange
        else if (highlightRoute) color = '#52c41a'; // Active Green
        
        const icon = createIcon(
            color,
            isDepot ? 'DEPOT' : 'POINT',
            p.sequence
        );
        
        L.marker([p.lat, p.lng], { icon })
         .addTo(markersLayer)
         .bindPopup(`
            <div class="font-sans text-slate-800">
                <div class="font-bold text-sm">${p.name}</div>
                <div class="text-xs text-slate-500 mt-1">
                   ${isDepot ? '区域分拨中心 (RDC)' : `订单量: ${p.demand} units`}
                </div>
            </div>
         `);
    });

    // 2. Draw Route Polyline (Always draw, style depends on highlightRoute)
    if (depot && deliveries.length > 0) {
        const latlngs: [number, number][] = [
            [depot.lat, depot.lng],
            ...deliveries.map(p => [p.lat, p.lng] as [number, number]),
            [depot.lat, depot.lng]
        ];

        // If highlighted: Blue, thick, solid
        // If not: Gray, thinner, dashed
        const polylineOptions: L.PolylineOptions = highlightRoute ? {
            color: '#1890ff',
            weight: 4,
            opacity: 0.8,
            dashArray: undefined,
            lineCap: 'round'
        } : {
            color: '#64748b',
            weight: 2,
            opacity: 0.6,
            dashArray: '5, 10',
            lineCap: 'round'
        };

        const polyline = L.polyline(latlngs, polylineOptions).addTo(map);
        
        // Always fit bounds to show the whole route context
        const bounds = L.latLngBounds(latlngs);
        map.fitBounds(bounds, { padding: [50, 50] });
        
        routeLineRef.current = polyline;
    }

  }, [points, highlightRoute]);

  return (
    <div className="w-full h-full bg-[#f8fafc] relative overflow-hidden rounded-lg border border-gray-200">
       {/* Map Container */}
       <div ref={mapContainerRef} className="absolute inset-0 z-0 bg-slate-100" />

       {/* Overlay Controls */}
       <div className="absolute bottom-4 left-4 z-[400] bg-white/90 backdrop-blur p-4 rounded-lg border border-gray-200 shadow-lg flex flex-col gap-2 text-xs text-gray-600 max-w-[200px]">
          <div className="flex items-center gap-2">
             <div className="w-3 h-3 bg-yellow-500 rounded-full border border-white shadow-sm"></div>
             <span>中央仓库 (新都基地)</span>
          </div>
          <div className="flex items-center gap-2">
             <div className={`w-3 h-3 rounded-full border border-white shadow-sm flex items-center justify-center text-[8px] text-white font-bold ${highlightRoute ? 'bg-green-500' : 'bg-slate-400'}`}>1</div>
             <span>配送顺序节点</span>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-6 h-0.5 ${highlightRoute ? 'bg-blue-500' : 'bg-slate-400 border-t border-dashed border-slate-400'}`}></div>
            <span>{highlightRoute ? 'VRPPD 优化路径' : '计划配送路线'}</span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-100 text-[10px] text-slate-400">
             Map data &copy; OpenStreetMap
          </div>
       </div>
       
       {/* Region Badge */}
       <div className="absolute top-4 right-4 z-[400] bg-white/90 backdrop-blur px-3 py-1.5 rounded-full border border-slate-200 shadow-sm flex items-center gap-2">
           <Layers size={14} className="text-slate-400"/>
           <span className="text-xs font-bold text-slate-700">Sichuan, Chengdu (CN)</span>
       </div>
    </div>
  );
};
