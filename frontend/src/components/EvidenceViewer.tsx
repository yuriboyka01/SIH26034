import React from 'react';
import { Camera, AlertCircle } from 'lucide-react';

interface EvidenceData {
  source_text?: string;
  confidence?: number;
  bbox?: number[];
}

interface EvidenceViewerProps {
  evidence?: EvidenceData;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({ evidence }) => {
  if (!evidence) {
    return (
      <div className="flex flex-col items-center justify-center p-4 bg-slate-50 border border-slate-200 border-dashed rounded-lg text-slate-400">
        <Camera className="w-6 h-6 mb-2 opacity-50" />
        <span className="text-xs">No evidence recorded</span>
      </div>
    );
  }

  const { source_text, confidence, bbox } = evidence;

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg overflow-hidden">
      <div className="px-3 py-2 bg-slate-100 border-b border-slate-200 flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-600">Extracted Evidence</span>
        {confidence !== undefined && (
          <span
            className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
              confidence > 0.8
                ? 'bg-emerald-100 text-emerald-700'
                : confidence > 0.5
                ? 'bg-amber-100 text-amber-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {(confidence * 100).toFixed(1)}% Conf
          </span>
        )}
      </div>

      <div className="p-3">
        {source_text ? (
          <div className="bg-white border border-slate-200 rounded p-2 mb-2 font-mono text-sm text-slate-800 break-words">
            "{source_text}"
          </div>
        ) : (
          <div className="text-sm text-slate-500 italic mb-2">No text extracted</div>
        )}

        {bbox ? (
          <div className="flex items-start gap-1.5 mt-2 bg-amber-50 p-2 rounded border border-amber-100">
            <AlertCircle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
            <p className="text-[10px] text-amber-700 leading-tight">
              Bounding box coordinates [x1,y1,x2,y2] recorded, but visual overlay is unavailable to prevent inaccurate coordinate mapping on scaled images.
            </p>
          </div>
        ) : (
          <div className="text-[10px] text-slate-400">No spatial region recorded.</div>
        )}
      </div>
    </div>
  );
};
