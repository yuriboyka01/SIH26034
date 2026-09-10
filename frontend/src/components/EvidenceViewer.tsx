import { useEffect, useRef } from 'react';
import { FileText, MapPin } from 'lucide-react';
import { StatusBadge } from './ui';

interface EvidenceData { source_text?: string; confidence?: number; bbox?: number[]; }

const STATUS_COLORS: Record<string, string> = {
  PASS: '#10B981', // --success
  FAIL: '#EF4444', // --danger
  REVIEW: '#F59E0B', // --warning
};

function EvidenceCrop({ imageUrl, bbox, status }: { imageUrl: string; bbox: number[]; status?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || bbox.length !== 4) return;
    const context = canvas.getContext('2d');
    if (!context) return;

    const image = new Image();
    image.onload = () => {
      const [x1, y1, x2, y2] = bbox;
      const boxW = Math.max(x2 - x1, 1);
      const boxH = Math.max(y2 - y1, 1);

      const padX = Math.max(boxW * 0.8, 30);
      const padY = Math.max(boxH * 0.8, 30);
      const cropX = Math.max(0, x1 - padX);
      const cropY = Math.max(0, y1 - padY);
      const cropW = Math.min(image.naturalWidth - cropX, boxW + padX * 2);
      const cropH = Math.min(image.naturalHeight - cropY, boxH + padY * 2);
      if (cropW <= 0 || cropH <= 0) return;

      const displayW = canvas.width;
      const displayH = canvas.height;
      context.clearRect(0, 0, displayW, displayH);
      context.drawImage(image, cropX, cropY, cropW, cropH, 0, 0, displayW, displayH);

      const sx = displayW / cropW;
      const sy = displayH / cropH;
      
      context.lineWidth = 3;
      context.strokeStyle = STATUS_COLORS[status || ''] || '#2563EB';
      context.shadowColor = 'rgba(0,0,0,0.3)';
      context.shadowBlur = 4;
      context.strokeRect((x1 - cropX) * sx, (y1 - cropY) * sy, boxW * sx, boxH * sy);
      
      context.fillStyle = (STATUS_COLORS[status || ''] || '#2563EB') + '22';
      context.shadowBlur = 0;
      context.fillRect((x1 - cropX) * sx, (y1 - cropY) * sy, boxW * sx, boxH * sy);
    };
    image.onerror = () => { };
    image.src = imageUrl;
  }, [imageUrl, bbox, status]);

  return (
    <div className="rounded-lg border border-[var(--line-strong)] overflow-hidden shadow-inner bg-[var(--surface-raised)] relative group">
      <canvas ref={canvasRef} width={280} height={160} className="w-full h-auto block" aria-label="Cropped evidence region" />
      <div className="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
        <div className="bg-[var(--surface)]/90 backdrop-blur-sm rounded-full p-2 shadow-sm">
          <MapPin size={16} className="text-[var(--text)]" />
        </div>
      </div>
    </div>
  );
}

export function EvidenceViewer({ evidence, imageUrl, status }: { evidence?: EvidenceData; imageUrl?: string; status?: string }) {
  if (!evidence) {
    return (
      <div className="flex items-center gap-2 p-4 bg-[var(--surface-raised)] rounded-lg border border-dashed border-[var(--line-strong)] text-sm text-[var(--text-muted)] italic">
        <FileText size={16} className="text-[var(--text-faint)]" /> No visual evidence region captured for this rule.
      </div>
    );
  }
  
  const confidence = evidence.confidence == null ? null : Math.round(evidence.confidence * 100);
  const state = confidence == null ? 'PENDING' : confidence >= 80 ? 'COMPLETE' : confidence >= 50 ? 'REVIEW' : 'ERROR';
  const hasCrop = Boolean(imageUrl && evidence.bbox && evidence.bbox.length === 4);

  return (
    <div className="mt-4 bg-[var(--surface-pale)] border border-[var(--line)] rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)] bg-[var(--surface)]/50">
        <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">Evidence Source Map</p>
        {confidence !== null && <StatusBadge value={state} label={`${confidence}% OCR Match`} />}
      </div>
      <div className="p-4 grid gap-4 lg:grid-cols-2">
        {hasCrop && <EvidenceCrop imageUrl={imageUrl!} bbox={evidence.bbox!} status={status} />}
        <div className="flex flex-col justify-center">
          {evidence.source_text ? (
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] mb-1.5">Detected Text</p>
              <blockquote className="border-l-2 border-[var(--brand)] pl-3 font-mono text-sm font-semibold text-[var(--text)] bg-[var(--surface)] py-1.5 rounded-r-md shadow-[inset_1px_0_0_rgba(0,0,0,0.02)]">
                {evidence.source_text}
              </blockquote>
            </div>
          ) : (
             <p className="text-sm italic text-[var(--text-muted)]">No text matched directly.</p>
          )}
          {evidence.bbox && (
            <p className="mt-4 flex items-center gap-1.5 text-xs font-medium text-[var(--text-muted)]">
              <MapPin size={14} className="text-[var(--brand)]" /> Mapped to product package
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
