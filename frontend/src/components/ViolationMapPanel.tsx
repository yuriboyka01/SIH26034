import { useEffect, useRef } from 'react';
import * as L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin } from 'lucide-react';
import { type GeoPointItem } from '../api/dashboard';
import { EmptyState } from './ui';

const STATUS_COLOR: Record<string, string> = {
  PASS: '#16a34a',
  FAIL: '#dc2626',
  REVIEW: '#d97706',
  NOT_ANALYSED: '#9ca3af',
};

function escapeHtml(input: string): string {
  const div = document.createElement('div');
  div.textContent = input;
  return div.innerHTML;
}

/**
 * Plots geo-tagged inspections on a real map, colored by their (already
 * merged, per-inspection) compliance status. Uses raw Leaflet with
 * circleMarker rather than react-leaflet + icon markers: circleMarker is
 * drawn as SVG, so there's no marker-icon asset path to misconfigure under
 * Vite — the single most common source of broken Leaflet integrations.
 */
export default function ViolationMapPanel({ points }: { points: GeoPointItem[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || points.length === 0) return;

    // Guard against double-init (e.g. React StrictMode's dev double-invoke).
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    const map = L.map(containerRef.current, { scrollWheelZoom: false });
    mapRef.current = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);

    points.forEach((point) => {
      const color = STATUS_COLOR[point.compliance_status] || STATUS_COLOR.NOT_ANALYSED;
      const marker = L.circleMarker([point.latitude, point.longitude], {
        radius: 9,
        color: '#ffffff',
        weight: 2,
        fillColor: color,
        fillOpacity: 0.9,
      }).addTo(map);

      const shopLine = point.establishment_name ? `${escapeHtml(point.establishment_name)}<br/>` : '';
      marker.bindPopup(
        `<div style="font-family: inherit; min-width: 180px; line-height: 1.5;">` +
          `<strong>${escapeHtml(point.brand)}</strong> — ${escapeHtml(point.product_name)}<br/>` +
          shopLine +
          `<span style="color:${color}; font-weight:700;">${escapeHtml(point.compliance_status)}</span><br/>` +
          `<a href="/inspections/${point.inspection_id}" style="color:#3F3A6B; font-weight:600;">View inspection &rarr;</a>` +
        `</div>`
      );
    });

    if (points.length === 1) {
      map.setView([points[0].latitude, points[0].longitude], 14);
    } else {
      map.fitBounds(L.latLngBounds(points.map((p) => [p.latitude, p.longitude])), { padding: [30, 30] });
    }

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [points]);

  if (points.length === 0) {
    return (
      <EmptyState
        icon={<MapPin size={28} />}
        title="No geo-tagged inspections yet"
        description="Capture GPS location when creating an inspection to see violations plotted on a map here."
      />
    );
  }

  return (
    <div className="p-3 sm:p-4">
      <div ref={containerRef} className="h-[360px] sm:h-[420px] w-full rounded-lg overflow-hidden border border-[var(--line)]" />
      <div className="mt-3 flex flex-wrap items-center gap-4 text-[11px] font-semibold text-[var(--text-muted)]">
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ background: STATUS_COLOR.FAIL }} /> Fail</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ background: STATUS_COLOR.REVIEW }} /> Review</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ background: STATUS_COLOR.PASS }} /> Pass</span>
      </div>
    </div>
  );
}
