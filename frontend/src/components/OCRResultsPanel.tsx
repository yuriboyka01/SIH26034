/**
 * OCRResultsPanel — displays OCR results for a single image with
 * bounding-box overlay rendered on a canvas over the image.
 */

import { useRef, useEffect } from 'react';
import type { ImageAnalysisResult, OCRBlock } from '../api/analysis';

interface Props {
  imageUrl: string;
  result: ImageAnalysisResult;
}

const QUALITY_COLOR: Record<string, string> = {
  GOOD: '#10b981',
  FAIR: '#f59e0b',
  POOR: '#ef4444',
};

const CONFIDENCE_COLORS = [
  '#6366f1', '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b', '#10b981',
];

function confidenceColor(index: number) {
  return CONFIDENCE_COLORS[index % CONFIDENCE_COLORS.length];
}

interface BBoxOverlayProps {
  imageUrl: string;
  blocks: OCRBlock[];
}

function BBoxOverlay({ imageUrl, blocks }: BBoxOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas) return;

    const draw = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Match canvas to rendered image dimensions
      const rect = img.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;

      // Scale factors (image may be displayed smaller than natural size)
      const scaleX = rect.width / img.naturalWidth;
      const scaleY = rect.height / img.naturalHeight;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      blocks.forEach((block, i) => {
        const [x1, y1, x2, y2] = block.bbox;
        const color = confidenceColor(i);

        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(
          x1 * scaleX, y1 * scaleY,
          (x2 - x1) * scaleX, (y2 - y1) * scaleY
        );

        // Confidence label badge
        const pct = Math.round(block.confidence * 100);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.85;
        const label = `${pct}%`;
        ctx.font = 'bold 11px sans-serif';
        const tw = ctx.measureText(label).width;
        ctx.fillRect(x1 * scaleX, y1 * scaleY - 16, tw + 8, 16);
        ctx.globalAlpha = 1;
        ctx.fillStyle = '#fff';
        ctx.fillText(label, x1 * scaleX + 4, y1 * scaleY - 3);
      });
    };

    if (img.complete) {
      draw();
    } else {
      img.addEventListener('load', draw);
      return () => img.removeEventListener('load', draw);
    }
  }, [blocks, imageUrl]);

  return (
    <div className="relative inline-block w-full">
      <img
        ref={imgRef}
        src={imageUrl}
        alt="Package label"
        className="w-full rounded-lg"
        style={{ display: 'block' }}
      />
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
      />
    </div>
  );
}

export default function OCRResultsPanel({ imageUrl, result }: Props) {
  const qStatus = result.quality?.status ?? 'UNKNOWN';
  const qColor = QUALITY_COLOR[qStatus] ?? '#6b7280';
  const blocks = result.ocr?.blocks ?? [];

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.1)',
      }}
    >
      {/* Image with bbox overlay */}
      <div className="p-4">
        {result.status === 'NOT_ANALYSED' ? (
          <div
            className="rounded-lg flex items-center justify-center h-40"
            style={{ background: 'rgba(255,255,255,0.05)' }}
          >
            <p style={{ color: 'rgba(255,255,255,0.4)' }}>Not yet analysed</p>
          </div>
        ) : (
          <BBoxOverlay imageUrl={imageUrl} blocks={blocks} />
        )}
      </div>

      {/* Quality badge */}
      {result.quality && (
        <div className="px-4 pb-3 flex flex-wrap gap-2 items-center">
          <span
            className="text-xs font-semibold px-3 py-1 rounded-full"
            style={{ background: qColor + '33', color: qColor, border: `1px solid ${qColor}55` }}
          >
            Quality: {qStatus}
          </span>
          {result.quality.issues.map((issue) => (
            <span
              key={issue}
              className="text-xs px-2 py-1 rounded-full"
              style={{ background: 'rgba(239,68,68,0.15)', color: '#fca5a5' }}
            >
              {issue.replace(/_/g, ' ')}
            </span>
          ))}
          {result.ocr?.processing_time_ms != null && (
            <span className="text-xs" style={{ color: 'rgba(255,255,255,0.4)' }}>
              {result.ocr.processing_time_ms} ms
            </span>
          )}
          {result.ocr?.preprocessing_applied && result.ocr.preprocessing_applied.length > 0 && (
            <span className="text-xs" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Preprocessing: {result.ocr.preprocessing_applied.join(', ')}
            </span>
          )}
        </div>
      )}

      {/* OCR Text Blocks */}
      {result.status === 'ERROR' && (
        <div
          className="mx-4 mb-4 p-3 rounded-lg text-sm"
          style={{ background: 'rgba(239,68,68,0.15)', color: '#fca5a5' }}
        >
          OCR failed: {result.error}
        </div>
      )}

      {blocks.length > 0 && (
        <div className="px-4 pb-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'rgba(255,255,255,0.5)' }}>
            Detected Text ({blocks.length} blocks)
          </h4>
          <div className="space-y-1.5 max-h-64 overflow-y-auto">
            {blocks.map((block, i) => (
              <div
                key={i}
                className="flex items-start gap-2 p-2 rounded-lg"
                style={{ background: 'rgba(255,255,255,0.04)' }}
              >
                <span
                  className="text-xs font-mono px-1.5 py-0.5 rounded shrink-0 mt-0.5"
                  style={{
                    background: confidenceColor(i) + '33',
                    color: confidenceColor(i),
                    minWidth: '38px',
                    textAlign: 'center',
                  }}
                >
                  {Math.round(block.confidence * 100)}%
                </span>
                <span className="text-sm" style={{ color: 'rgba(255,255,255,0.85)' }}>
                  {block.text}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {result.status === 'OK' && blocks.length === 0 && (
        <div className="px-4 pb-4">
          <p className="text-sm" style={{ color: 'rgba(255,255,255,0.4)' }}>
            No text detected. Try uploading a clearer image.
          </p>
        </div>
      )}
    </div>
  );
}
