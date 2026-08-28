import { FileText, MapPin } from 'lucide-react';
import { StatusBadge } from './ui';

interface EvidenceData { source_text?: string; confidence?: number; bbox?: number[]; }

export function EvidenceViewer({ evidence }: { evidence?: EvidenceData }) {
  if (!evidence) return <div className="app-panel flex items-center gap-2 p-3 text-xs text-[var(--text-faint)]"><FileText size={15} /> No source evidence is attached to this result.</div>;
  const confidence = evidence.confidence == null ? null : Math.round(evidence.confidence * 100);
  const state = confidence == null ? 'PENDING' : confidence >= 80 ? 'COMPLETE' : confidence >= 50 ? 'REVIEW' : 'ERROR';
  return <section className="app-panel overflow-hidden"><div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--line)] px-3 py-2"><p className="app-kicker">Evidence reference</p>{confidence !== null && <StatusBadge value={state} label={`${confidence}% confidence`} />}</div><div className="p-3">{evidence.source_text ? <blockquote className="border-l-2 border-[#5b8cff] pl-3 font-mono text-xs leading-relaxed text-[#d5deec]">{evidence.source_text}</blockquote> : <p className="text-xs italic text-[var(--text-faint)]">No text was retained for this evidence reference.</p>}{evidence.bbox && <p className="mt-3 flex items-center gap-1.5 text-[11px] text-[var(--text-faint)]"><MapPin size={12} /> Source region recorded on the uploaded image.</p>}</div></section>;
}
