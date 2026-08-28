import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AlertCircle, ArrowLeft, Download, FileText, ImageIcon, Loader2, RefreshCw, ScanText, Trash2, Upload, X } from 'lucide-react';
import { deleteInspectionImage, getInspection, uploadInspectionImage, type Inspection, type InspectionImage } from '../api/inspections';
import { analyzeInspection, getAnalysisResults, type AnalysisResponse } from '../api/analysis';
import { getProductInfo, type ProductInfo } from '../api/product_info';
import { getComplianceReports, runComplianceAnalysis, type ComplianceReport } from '../api/compliance';
import { downloadReport } from '../api/reports';
import OCRResultsPanel from '../components/OCRResultsPanel';
import ProductInfoPanel from '../components/ProductInfoPanel';
import { ComplianceResultsPanel } from '../components/ComplianceResultsPanel';
import { Alert, EmptyState, LoadingState, ProgressStages, SectionHeader, StatusBadge } from '../components/ui';

type AnalysisPhase = 'idle' | 'ocr' | 'extraction' | 'rules';

export default function InspectionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [inspection, setInspection] = useState<Inspection | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [success, setSuccess] = useState('');
  const [uploading, setUploading] = useState(false); const [uploadProgress, setUploadProgress] = useState(0); const [dragOver, setDragOver] = useState(false); const [deleteCandidate, setDeleteCandidate] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null); const [productInfo, setProductInfo] = useState<ProductInfo | null>(null); const [complianceReports, setComplianceReports] = useState<ComplianceReport[]>([]); const [analysing, setAnalysing] = useState(false); const [analysisPhase, setAnalysisPhase] = useState<AnalysisPhase>('idle'); const [analysisProgress, setAnalysisProgress] = useState(0); const [processedImageCount, setProcessedImageCount] = useState(0); const [analysisError, setAnalysisError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchInspection = useCallback(async () => { if (!id) return; try { const [record, info, compliance] = await Promise.all([getInspection(id), getProductInfo(id).catch(() => null), getComplianceReports(id).catch(() => null)]); setInspection(record); setProductInfo(info?.product_info_list?.[0] || null); setComplianceReports(compliance?.reports || []); } catch { setError('The inspection record could not be loaded. Please return to the register and try again.'); } finally { setLoading(false); } }, [id]);
  useEffect(() => { fetchInspection(); if (id) getAnalysisResults(id).then(setAnalysisResult).catch(() => undefined); }, [fetchInspection, id]);
  const flash = (message: string) => { setSuccess(message); window.setTimeout(() => setSuccess(''), 3000); };
  const handleFileUpload = async (files: FileList | null) => { if (!files?.length || !id) return; setError(''); setUploading(true); setUploadProgress(0); try { for (const file of Array.from(files)) { if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { setError(`${file.name}: only JPG, PNG, and WEBP evidence is supported.`); continue; } if (file.size > 10 * 1024 * 1024) { setError(`${file.name}: file size exceeds the 10 MB limit.`); continue; } await uploadInspectionImage(id, file, 'OTHER', setUploadProgress); } await fetchInspection(); flash('Evidence uploaded. Run analysis when the evidence set is ready.'); } catch (err: unknown) { const detail = err as { response?: { data?: { error?: { message?: string } } } }; setError(detail.response?.data?.error?.message || 'Evidence could not be uploaded. Please try again.'); } finally { setUploading(false); setUploadProgress(0); if (fileInputRef.current) fileInputRef.current.value = ''; } };
  const confirmDelete = async () => { if (!id || !deleteCandidate) return; try { await deleteInspectionImage(id, deleteCandidate); setDeleteCandidate(null); setAnalysisResult(null); await fetchInspection(); flash('Evidence image deleted.'); } catch (err: unknown) { const detail = err as { response?: { data?: { error?: { message?: string } } } }; setError(detail.response?.data?.error?.message || 'Evidence could not be deleted.'); } };
  const handleAnalyze = async () => {
    if (!id) return;
    setAnalysisError(''); setAnalysing(true); setAnalysisPhase('ocr'); setAnalysisProgress(12); setProcessedImageCount(0);
    let progressTimer: number | undefined;
    try {
      // OCR is a synchronous server operation, so advance only within the OCR phase
      // until its response arrives instead of claiming that later stages are complete.
      progressTimer = window.setInterval(() => setAnalysisProgress((progress) => Math.min(progress + 3, 68)), 900);
      const analysis = await analyzeInspection(id);
      window.clearInterval(progressTimer); progressTimer = undefined;
      setAnalysisResult(analysis); setProcessedImageCount(analysis.images.length); setAnalysisPhase('extraction'); setAnalysisProgress(74);
      const info = await getProductInfo(id);
      setProductInfo(info.product_info_list?.[0] || null); setAnalysisPhase('rules'); setAnalysisProgress(88);
      const compliance = await runComplianceAnalysis(id);
      setComplianceReports(compliance.reports || []); setAnalysisProgress(100);
      await fetchInspection(); flash('Evidence analysis and rule evaluation completed.');
    } catch (err: unknown) {
      const detail = err as { response?: { data?: { error?: { message?: string } } } };
      setAnalysisError(detail.response?.data?.error?.message || 'Analysis could not be completed. Review the evidence and try again.');
    } finally {
      if (progressTimer) window.clearInterval(progressTimer);
      setAnalysing(false); setAnalysisPhase('idle');
    }
  };
  if (loading) return <LoadingState label="Opening inspection workspace" />;
  if (!inspection) return <EmptyState icon={<AlertCircle size={28} />} title="Inspection unavailable" description="The requested inspection could not be found or loaded." action={<Link to="/inspections" className="ui-button-secondary">Back to register</Link>} />;

  const hasImages = inspection.images.length > 0;
  // A stored error/placeholder result is not a completed analysis. It must keep the
  // first-run action available so the user is not presented with only "Re-run".
  const hasSuccessfulAnalysis = analysisResult?.images.some((result) => result.status === 'OK') || false;
  const hasReports = complianceReports.length > 0;
  const phaseIndex: Record<AnalysisPhase, number> = { idle: 0, ocr: 1, extraction: 2, rules: 3 };
  const phaseCompleteThrough: Record<AnalysisPhase, number> = { idle: -1, ocr: 0, extraction: 1, rules: 2 };
  const stages = ['Evidence', 'OCR', 'Extraction', 'Rules', 'Findings', 'Report']; const activeIndex = analysing ? phaseIndex[analysisPhase] : !hasImages ? 0 : hasReports ? 5 : hasSuccessfulAnalysis ? 3 : 0; const completeThrough = analysing ? phaseCompleteThrough[analysisPhase] : hasReports ? 4 : hasSuccessfulAnalysis ? 2 : hasImages ? 0 : -1;
  return <div className="space-y-6"><Link to="/inspections" className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[#bcd4ff]"><ArrowLeft size={16} /> Back to inspection register</Link>
    <section className="app-surface overflow-hidden"><div className="flex flex-wrap items-start justify-between gap-5 px-5 py-5 sm:px-6"><div><p className="app-kicker">Inspection · <span className="font-mono">{inspection.inspection_number}</span></p><div className="mt-2 flex flex-wrap items-center gap-3"><h2 className="text-xl font-semibold tracking-tight text-[var(--text)] sm:text-2xl">{inspection.product_name}</h2><StatusBadge value={inspection.status} /></div><p className="mt-2 text-sm text-[var(--text-muted)]">{inspection.brand} <span className="mx-2 text-[var(--text-faint)]">·</span><span className="font-mono text-xs">Opened {new Date(inspection.created_at).toLocaleString()}</span></p></div><div className="flex flex-wrap gap-2">{hasReports && <><button onClick={() => downloadReport(id!, 'pdf')} className="ui-button-secondary"><FileText size={16} /> PDF</button><button onClick={() => downloadReport(id!, 'docx')} className="ui-button-secondary"><Download size={16} /> DOCX</button></>}{hasImages && <button onClick={handleAnalyze} disabled={analysing} className="ui-button-primary">{analysing ? <><Loader2 size={16} className="animate-spin" /> Analysing evidence…</> : hasSuccessfulAnalysis ? <><RefreshCw size={16} /> Re-run analysis</> : <><ScanText size={16} /> Analyze evidence</>}</button>}</div></div><div className="border-t border-[var(--line)] px-5 py-4 sm:px-6"><ProgressStages stages={stages} activeIndex={activeIndex} completeThrough={completeThrough} /></div></section>
    {error && <Alert tone="error">{error}<button aria-label="Dismiss" className="ml-auto -mr-1 text-current" onClick={() => setError('')}><X size={16} /></button></Alert>}{analysisError && <Alert tone="error">{analysisError}<button aria-label="Dismiss" className="ml-auto -mr-1 text-current" onClick={() => setAnalysisError('')}><X size={16} /></button></Alert>}{success && <Alert tone="success">{success}</Alert>}
    {analysing && <AnalysisProgress phase={analysisPhase} progress={analysisProgress} imageCount={inspection.images.length} processedImageCount={processedImageCount} />}
    <section className="grid gap-5 xl:grid-cols-[minmax(0,.95fr)_minmax(0,1.05fr)]"><div className="space-y-5"><section className="app-surface overflow-hidden"><SectionHeader eyebrow="Evidence" title="Evidence collection" description="Upload package images to establish the inspection record." /><div className="p-4"><div onDragOver={(event) => { event.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)} onDrop={(event) => { event.preventDefault(); setDragOver(false); handleFileUpload(event.dataTransfer.files); }} onClick={() => fileInputRef.current?.click()} className={`cursor-pointer border border-dashed p-6 text-center transition-colors ${dragOver ? 'border-[#7ea6ff] bg-[#111d31]' : 'border-[var(--line-strong)] bg-[#0a0f18] hover:border-[#5873a6]'}`}>{uploading ? <div><Loader2 size={24} className="mx-auto animate-spin text-[#8cc1ff]" /><p className="mt-3 text-sm text-[var(--text)]">Uploading evidence · {uploadProgress}%</p><div className="mx-auto mt-3 h-1 w-44 overflow-hidden bg-[#1a2535]"><div className="h-full bg-[#5b8cff]" style={{ width: `${uploadProgress}%` }} /></div></div> : <><Upload size={25} className="mx-auto text-[var(--text-faint)]" /><p className="mt-3 text-sm font-semibold text-[var(--text)]">Add package evidence</p><p className="mt-1 text-xs text-[var(--text-muted)]">Drop JPG, PNG, or WEBP files here · maximum 10 MB per image</p></>}<input ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.webp" multiple className="hidden" onChange={(event) => handleFileUpload(event.target.files)} /></div></div></section>
      {hasImages ? <div className="space-y-5">{inspection.images.map((image) => <EvidenceItem key={image.id} image={image} result={analysisResult?.images.find((result) => result.image_id === image.id) || null} pendingDelete={deleteCandidate === image.id} onAskDelete={() => setDeleteCandidate(image.id)} onCancelDelete={() => setDeleteCandidate(null)} onConfirmDelete={confirmDelete} />)}</div> : <EmptyState icon={<ImageIcon size={28} />} title="No evidence attached" description="Upload a package image to begin OCR extraction and compliance analysis." />}</div>
      <aside className="space-y-5"><ProductInfoPanel productInfo={productInfo} /><ComplianceResultsPanel reports={complianceReports} isAnalyzing={analysing} />{hasReports && <section className="app-surface overflow-hidden"><SectionHeader eyebrow="Report" title="Official report ready" description="The report includes the inspection identity, evidence-linked rules, and current compliance outcome." /><div className="flex flex-wrap gap-2 p-4"><button onClick={() => downloadReport(id!, 'pdf')} className="ui-button-secondary"><FileText size={16} /> Download PDF</button><button onClick={() => downloadReport(id!, 'docx')} className="ui-button-secondary"><Download size={16} /> Download DOCX</button></div></section>}</aside></section>
  </div>;
}

function AnalysisProgress({ phase, progress, imageCount, processedImageCount }: { phase: AnalysisPhase; progress: number; imageCount: number; processedImageCount: number }) {
  const phaseCopy: Record<Exclude<AnalysisPhase, 'idle'>, { title: string; description: string }> = {
    ocr: { title: 'Reading package evidence', description: `Running image-quality checks and OCR for ${imageCount} uploaded ${imageCount === 1 ? 'image' : 'images'}.` },
    extraction: { title: 'Extracting package declarations', description: 'Saving the text and matching label details to their source evidence.' },
    rules: { title: 'Evaluating compliance rules', description: 'Checking extracted declarations against the applicable legal-metrology rules.' },
  };
  const current = phaseCopy[phase === 'idle' ? 'ocr' : phase];
  const steps: Array<{ phase: Exclude<AnalysisPhase, 'idle'>; label: string }> = [{ phase: 'ocr', label: 'OCR & image quality' }, { phase: 'extraction', label: 'Declaration extraction' }, { phase: 'rules', label: 'Rule evaluation' }];
  const order: Record<AnalysisPhase, number> = { idle: 0, ocr: 1, extraction: 2, rules: 3 };
  return <section className="app-surface overflow-hidden" aria-live="polite"><div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"><div className="flex items-start gap-3"><Loader2 size={19} className="mt-0.5 shrink-0 animate-spin text-[#8cc1ff]" /><div><p className="text-sm font-semibold text-[var(--text)]">{current.title}</p><p className="mt-1 text-xs leading-relaxed text-[var(--text-muted)]">{current.description}</p></div></div><div className="text-right"><span className="block font-mono text-sm font-semibold text-[#b9d6ff]">{progress}%</span><span className="font-mono text-[11px] text-[var(--text-muted)]">{processedImageCount} / {imageCount} images processed</span></div></div><div className="h-1.5 bg-[#182131]"><div className="h-full bg-[#5b8cff] transition-[width] duration-500" style={{ width: `${progress}%` }} /></div><ol className="grid gap-2 px-5 py-3 text-xs sm:grid-cols-3">{steps.map((step) => <li key={step.phase} className={`flex items-center gap-2 ${order[step.phase] < order[phase] ? 'text-[#8ce0b5]' : step.phase === phase ? 'text-[#cce4ff]' : 'text-[var(--text-faint)]'}`}><span className={`grid h-5 w-5 place-items-center rounded-full border text-[10px] ${order[step.phase] < order[phase] ? 'border-[#35c98a] bg-[#35c98a]/10' : step.phase === phase ? 'border-[#5b8cff] bg-[#5b8cff]/10' : 'border-[var(--line-strong)]'}`}>{order[step.phase] < order[phase] ? '✓' : order[step.phase]}</span>{step.label}</li>)}</ol></section>;
}

function EvidenceItem({ image, result, pendingDelete, onAskDelete, onCancelDelete, onConfirmDelete }: { image: InspectionImage; result: AnalysisResponse['images'][number] | null; pendingDelete: boolean; onAskDelete: () => void; onCancelDelete: () => void; onConfirmDelete: () => void }) {
  return <section className="app-surface overflow-hidden"><header className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--line)] px-4 py-3"><div className="min-w-0"><p className="truncate text-sm font-semibold text-[var(--text)]">{image.original_filename}</p><p className="mt-1 font-mono text-[10px] uppercase tracking-wide text-[var(--text-faint)]">{image.image_type} · {(image.file_size / 1024).toFixed(0)} KB</p></div>{pendingDelete ? <div className="flex items-center gap-2"><span className="text-xs text-[#ffc4c4]">Remove this evidence?</span><button className="ui-button-danger !min-h-8 !px-2 !text-xs" onClick={onConfirmDelete}>Delete</button><button className="ui-icon-button" onClick={onCancelDelete} aria-label="Cancel delete"><X size={15} /></button></div> : <button className="ui-icon-button hover:!text-[#ffb4b4]" onClick={onAskDelete} aria-label={`Delete ${image.original_filename}`}><Trash2 size={16} /></button>}</header><div className="p-4">{result ? <OCRResultsPanel imageUrl={image.url} result={result} /> : <div className="overflow-hidden rounded-md border border-[var(--line)] bg-[#080d15]"><img src={image.url} alt={image.original_filename} className="max-h-[520px] w-full object-contain" loading="lazy" /><div className="border-t border-[var(--line)] px-4 py-3"><p className="text-sm font-semibold text-[var(--text)]">Evidence ready for analysis</p><p className="mt-1 text-xs text-[var(--text-muted)]">Run analysis to extract OCR declarations and evaluate applicable rules.</p></div></div>}</div></section>;
}
