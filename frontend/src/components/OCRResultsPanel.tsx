import { useEffect, useRef } from 'react';
import { MapPin, Timer, Scan } from 'lucide-react';
import type { ImageAnalysisResult, OCRBlock } from '../api/analysis';
import { StatusBadge } from './ui';

function EvidenceImage({ imageUrl, blocks }: { imageUrl: string; blocks: OCRBlock[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null); 
  const imageRef = useRef<HTMLImageElement>(null);
  
  useEffect(() => { 
    const image = imageRef.current; 
    const canvas = canvasRef.current; 
    if (!image || !canvas) return; 
    
    const draw = () => { 
      const context = canvas.getContext('2d'); 
      if (!context || !image.naturalWidth) return; 
      const rect = image.getBoundingClientRect(); 
      canvas.width = rect.width; 
      canvas.height = rect.height; 
      context.clearRect(0, 0, canvas.width, canvas.height); 
      
      const sx = rect.width / image.naturalWidth; 
      const sy = rect.height / image.naturalHeight; 
      
      blocks.forEach((block, index) => { 
        const [x1, y1, x2, y2] = block.bbox; 
        const x = x1 * sx; 
        const y = y1 * sy; 
        const width = (x2 - x1) * sx; 
        const height = (y2 - y1) * sy; 
        
        // Premium bounding box style
        context.lineWidth = 2; 
        context.strokeStyle = '#2563EB'; // Brand Royal Blue
        context.shadowColor = 'rgba(37, 99, 235, 0.4)';
        context.shadowBlur = 8;
        context.strokeRect(x, y, width, height); 
        
        // Soft fill
        context.fillStyle = 'rgba(37, 99, 235, 0.1)';
        context.fillRect(x, y, width, height);
        
        // Badge
        context.shadowBlur = 0;
        context.fillStyle = '#2563EB'; 
        const badgeWidth = 24;
        const badgeHeight = 18;
        context.beginPath();
        context.roundRect(x, Math.max(0, y - badgeHeight - 2), badgeWidth, badgeHeight, 4);
        context.fill();
        
        // Badge Text
        context.font = '700 11px Inter, sans-serif'; 
        context.fillStyle = '#FFFFFF'; 
        context.fillText(String(index + 1), x + 7, Math.max(12, y - 6)); 
      }); 
    }; 
    
    if (image.complete) draw(); else image.addEventListener('load', draw); 
    const observer = new ResizeObserver(draw); observer.observe(image); 
    return () => { image.removeEventListener('load', draw); observer.disconnect(); }; 
  }, [blocks, imageUrl]);

  return (
    <div className="relative overflow-hidden rounded-xl border border-[var(--line-strong)] bg-[var(--surface)] shadow-inner">
      <img ref={imageRef} src={imageUrl} alt="Inspection evidence with detected OCR regions" className="block max-h-[460px] w-full object-contain" />
      <canvas ref={canvasRef} className="pointer-events-none absolute inset-0 h-full w-full" />
    </div>
  );
}

export default function OCRResultsPanel({ imageUrl, result }: { imageUrl: string; result: ImageAnalysisResult }) {
  const blocks = result.ocr?.blocks || []; 
  const average = blocks.length ? Math.round((blocks.reduce((sum, block) => sum + block.confidence, 0) / blocks.length) * 100) : null;
  
  if (result.status === 'NOT_ANALYSED') {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center bg-[var(--surface-raised)] border border-dashed border-[var(--line-strong)] rounded-xl h-full">
        <div className="w-12 h-12 bg-[var(--surface)] rounded-full shadow-sm border border-[var(--line)] flex items-center justify-center mb-4">
          <Scan size={24} className="text-[var(--text-faint)]" />
        </div>
        <p className="text-sm font-bold text-[var(--text)]">OCR pending</p>
        <p className="mt-2 max-w-xs text-xs leading-relaxed text-[var(--text-muted)]">Run inspection analysis to detect declarations and map them to the source evidence.</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <EvidenceImage imageUrl={imageUrl} blocks={blocks} />
      </div>
      
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-[var(--surface-raised)] rounded-lg p-3 border border-[var(--line)]">
          <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">Regions</p>
          <p className="mt-1 font-mono text-xl font-bold text-[var(--text)]">{blocks.length}</p>
        </div>
        <div className="bg-[var(--surface-raised)] rounded-lg p-3 border border-[var(--line)]">
          <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">Confidence</p>
          <p className="mt-1 font-mono text-xl font-bold text-[var(--brand)]">{average === null ? '—' : `${average}%`}</p>
        </div>
        <div className="bg-[var(--surface-raised)] rounded-lg p-3 border border-[var(--line)] flex flex-col justify-between">
          <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">Time</p>
          <p className="mt-1 font-mono text-sm font-semibold text-[var(--text-muted)] flex items-center gap-1.5">
            <Timer size={14} />{result.ocr?.processing_time_ms == null ? '—' : `${result.ocr.processing_time_ms} ms`}
          </p>
        </div>
      </div>
      
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-bold text-[var(--text)]">Detected text layer</p>
          {result.quality && <StatusBadge value={result.quality.status === 'GOOD' ? 'COMPLETE' : result.quality.status === 'FAIR' ? 'REVIEW' : 'ERROR'} label={`Quality: ${result.quality.status}`} />}
        </div>
        
        {result.status === 'ERROR' ? (
          <div className="p-4 bg-[var(--danger-soft)] rounded-xl border border-[var(--danger-soft)] text-[var(--danger)] text-sm font-semibold">
            {result.error || 'OCR could not process this evidence.'}
          </div>
        ) : blocks.length ? (
          <div className="overflow-y-auto flex-1 pr-2 space-y-2 -mr-2">
            {blocks.map((block, index) => (
              <div key={`${block.text}-${index}`} className="flex gap-3 rounded-lg border border-[var(--line)] bg-[var(--surface)] p-3 shadow-sm hover:border-[var(--brand-soft)] transition-colors group">
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-[var(--brand-soft)] font-mono text-[11px] font-bold text-[var(--brand)]">
                  {index + 1}
                </span>
                <div className="min-w-0">
                  <p className="break-words text-sm font-medium text-[var(--text)]">{block.text}</p>
                  <div className="mt-1.5 flex items-center gap-3">
                    <span className="font-mono text-[10px] font-bold text-[var(--text-faint)] bg-[var(--surface-raised)] px-1.5 py-0.5 rounded">
                      {Math.round(block.confidence * 100)}% conf
                    </span>
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[var(--brand)] opacity-0 group-hover:opacity-100 transition-opacity">
                      <MapPin size={10} /> mapped
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-[var(--text-muted)] p-4 bg-[var(--surface-raised)] rounded-xl text-center">
            No text was detected. Upload a clearer image and run analysis again.
          </p>
        )}
      </div>
    </div>
  );
}
